"""Test Harness for OS/ONS MCP Server Evaluation

This module provides the infrastructure to run evaluation questions through
the MCP server and score the results.

Usage:
    python -m tests.evaluation.harness [--questions=basic,intermediate] [--output=results.json]
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from .questions import (
    EvaluationQuestion,
    ALL_QUESTIONS,
    BASIC_QUESTIONS,
    INTERMEDIATE_QUESTIONS,
    ADVANCED_QUESTIONS,
    EDGE_CASE_QUESTIONS,
    AMBIGUOUS_QUESTIONS,
    Difficulty,
    Intent,
    get_questions,
    get_question_summary,
)
from .rubric import (
    Rubric,
    QuestionScore,
    DimensionScore,
    EvaluationResult,
    ScoreLevel,
    RUBRIC_DESCRIPTION,
)

# Import MCP server components
try:
    from tools.query_router import route_query, _classify_query, QueryIntent
    from tools.geography_tools import search_geographic_areas
    from tools.statistics_tools import get_statistics, list_ons_datasets, compare_areas
    from utils.audit_logger import AuditLogger, AuditRecord, audit_query
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import MCP components: {e}")
    IMPORTS_AVAILABLE = False


@dataclass
class TestResult:
    """Result of running a single test"""
    question: EvaluationQuestion
    score: QuestionScore
    audit_record: Optional[AuditRecord] = None
    raw_responses: List[Dict[str, Any]] = field(default_factory=list)
    tool_calls: List[str] = field(default_factory=list)
    detected_intent: Optional[str] = None
    detected_confidence: float = 0.0
    duration_ms: float = 0.0
    error: Optional[str] = None


class EvaluationHarness:
    """
    Harness for running evaluation tests against the MCP server.

    This harness:
    1. Runs each question through the query router
    2. Executes the recommended tools
    3. Collects audit logs
    4. Scores results against the rubric
    """

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        verbose: bool = False,
    ):
        self.log_dir = log_dir or Path("logs/evaluation")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self.rubric = Rubric()
        self.audit_logger = AuditLogger(log_dir=self.log_dir / "audit")
        self.results: List[TestResult] = []

    async def run_single_question(
        self,
        question: EvaluationQuestion,
    ) -> TestResult:
        """Run a single evaluation question and return the result"""

        start_time = time.time()
        tool_calls: List[str] = []
        raw_responses: List[Dict[str, Any]] = []
        detected_intent: Optional[str] = None
        detected_confidence: float = 0.0
        error: Optional[str] = None

        # Start audit
        audit_id = self.audit_logger.start_query(
            question.question,
            metadata={"question_id": question.id, "expected_intent": question.intent.value},
        )

        try:
            # Step 1: Run route_query
            if question.question.strip():  # Skip empty queries
                routing_result = await route_query(question.question)
                routing_data = json.loads(routing_result)
                tool_calls.append("route_query")
                raw_responses.append({"tool": "route_query", "response": routing_data})

                detected_intent = routing_data.get("intent")
                detected_confidence = routing_data.get("confidence", 0.0)
                recommended_tool = routing_data.get("recommended_tool")

                # Record routing in audit
                self.audit_logger.record_routing(
                    intent=detected_intent or "unknown",
                    confidence=detected_confidence,
                    recommended_tool=recommended_tool or "unknown",
                    workflow_steps=routing_data.get("workflow_steps", []),
                )

                # Step 2: Execute recommended tool (for place lookups)
                if recommended_tool == "search_geographic_areas":
                    params = routing_data.get("recommended_parameters", {})
                    query = params.get("query", question.question)
                    level = params.get("level", "local_auth")

                    search_result = await search_geographic_areas(query, level)
                    search_data = json.loads(search_result)
                    tool_calls.append("search_geographic_areas")
                    raw_responses.append({"tool": "search_geographic_areas", "response": search_data})

                    # Record tool call in audit
                    self.audit_logger.record_tool_call(
                        tool_name="search_geographic_areas",
                        inputs={"query": query, "level": level},
                        outputs=search_data,
                        duration_ms=0,  # Will be calculated
                        success="error" not in str(search_data).lower(),
                    )

                elif recommended_tool == "list_ons_datasets":
                    datasets_result = await list_ons_datasets()
                    datasets_data = json.loads(datasets_result)
                    tool_calls.append("list_ons_datasets")
                    raw_responses.append({"tool": "list_ons_datasets", "response": datasets_data})

                # Record final response
                final_response = json.dumps(raw_responses[-1]["response"] if raw_responses else {})
                self.audit_logger.record_response(final_response)

        except Exception as e:
            error = str(e)
            self.audit_logger.record_error(error)

        # End audit
        audit_record = self.audit_logger.end_query()
        duration_ms = (time.time() - start_time) * 1000

        # Score the result
        score = self._score_result(
            question=question,
            detected_intent=detected_intent,
            detected_confidence=detected_confidence,
            tool_calls=tool_calls,
            raw_responses=raw_responses,
            error=error,
        )

        result = TestResult(
            question=question,
            score=score,
            audit_record=audit_record,
            raw_responses=raw_responses,
            tool_calls=tool_calls,
            detected_intent=detected_intent,
            detected_confidence=detected_confidence,
            duration_ms=duration_ms,
            error=error,
        )

        if self.verbose:
            self._print_result(result)

        return result

    def _score_result(
        self,
        question: EvaluationQuestion,
        detected_intent: Optional[str],
        detected_confidence: float,
        tool_calls: List[str],
        raw_responses: List[Dict[str, Any]],
        error: Optional[str],
    ) -> QuestionScore:
        """Score a test result against the rubric"""

        dimensions: List[DimensionScore] = []

        # 1. Intent Recognition
        intent_score = self.rubric.score_intent_recognition(
            expected_intent=question.intent.value,
            detected_intent=detected_intent,
            confidence=detected_confidence,
        )
        dimensions.append(intent_score)

        # 2. Tool Selection
        tool_score = self.rubric.score_tool_selection(
            required_tools=question.expected.required_tools,
            forbidden_tools=question.expected.forbidden_tools,
            actual_tools=tool_calls,
        )
        dimensions.append(tool_score)

        # 3. Efficiency
        efficiency_score = self.rubric.score_efficiency(
            actual_tool_calls=len(tool_calls),
            max_expected_calls=question.expected.max_tool_calls,
        )
        dimensions.append(efficiency_score)

        # 4. Response Quality
        # Combine all responses for checking
        full_response = json.dumps(raw_responses)
        quality_score = self.rubric.score_response_quality(
            response=full_response,
            required_keywords=question.expected.required_keywords,
            forbidden_keywords=question.expected.forbidden_keywords,
            expected_values=question.expected.expected_values,
        )
        dimensions.append(quality_score)

        # 5. Error Handling
        error_score = self.rubric.score_error_handling(
            had_errors=error is not None,
            error_messages=[error] if error else [],
            graceful_handling="traceback" not in str(error).lower() if error else True,
        )
        dimensions.append(error_score)

        # Calculate total
        total_score = sum(d.points for d in dimensions)

        return QuestionScore(
            question_id=question.id,
            question_text=question.question,
            total_score=total_score,
            dimensions=dimensions,
            tool_calls=tool_calls,
            response_summary=full_response[:500] if raw_responses else "",
        )

    def _print_result(self, result: TestResult) -> None:
        """Print a single result to console"""
        status = "✓" if result.score.percentage >= 75 else "✗"
        print(f"{status} [{result.question.id}] {result.question.question[:50]}")
        print(f"   Score: {result.score.total_score:.0f}/100 ({result.score.percentage:.0f}%)")
        print(f"   Intent: {result.detected_intent} (expected: {result.question.intent.value})")
        print(f"   Tools: {' → '.join(result.tool_calls)}")
        if result.error:
            print(f"   Error: {result.error[:100]}")
        print()

    async def run_questions(
        self,
        questions: List[EvaluationQuestion],
    ) -> List[TestResult]:
        """Run multiple questions and return results"""
        results = []
        for i, question in enumerate(questions, 1):
            if self.verbose:
                print(f"\n[{i}/{len(questions)}] Running: {question.question[:60]}...")
            result = await self.run_single_question(question)
            results.append(result)
        return results

    async def run_evaluation(
        self,
        difficulty: Optional[Difficulty] = None,
        intent: Optional[Intent] = None,
        question_ids: Optional[List[str]] = None,
    ) -> EvaluationResult:
        """Run a complete evaluation and return summary results"""

        # Select questions
        if question_ids:
            questions = [q for q in ALL_QUESTIONS if q.id in question_ids]
        else:
            questions = get_questions(intent=intent, difficulty=difficulty)

        if not questions:
            raise ValueError("No questions selected for evaluation")

        print(f"\n{'=' * 60}")
        print(f"OS/ONS MCP Server Evaluation")
        print(f"{'=' * 60}")
        print(f"Questions: {len(questions)}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"{'=' * 60}\n")

        # Run all questions
        self.results = await self.run_questions(questions)

        # Calculate summary
        total_score = sum(r.score.total_score for r in self.results)
        max_score = len(self.results) * 100
        percentage = (total_score / max_score) * 100 if max_score > 0 else 0

        # Score by difficulty
        by_difficulty: Dict[str, float] = {}
        for diff in Difficulty:
            diff_results = [r for r in self.results if r.question.difficulty == diff]
            if diff_results:
                diff_score = sum(r.score.total_score for r in diff_results)
                diff_max = len(diff_results) * 100
                by_difficulty[diff.value] = (diff_score / diff_max) * 100

        # Score by intent
        by_intent: Dict[str, float] = {}
        for intent_type in Intent:
            intent_results = [r for r in self.results if r.question.intent == intent_type]
            if intent_results:
                intent_score = sum(r.score.total_score for r in intent_results)
                intent_max = len(intent_results) * 100
                by_intent[intent_type.value] = (intent_score / intent_max) * 100

        # Determine overall level
        if percentage >= 90:
            level = ScoreLevel.EXCELLENT
        elif percentage >= 75:
            level = ScoreLevel.GOOD
        elif percentage >= 60:
            level = ScoreLevel.ACCEPTABLE
        elif percentage >= 40:
            level = ScoreLevel.POOR
        else:
            level = ScoreLevel.FAIL

        # Build result
        result = EvaluationResult(
            timestamp=datetime.now().isoformat(),
            total_questions=len(self.results),
            total_score=total_score,
            max_score=max_score,
            percentage=percentage,
            level=level,
            question_scores=[r.score for r in self.results],
            by_difficulty=by_difficulty,
            by_intent=by_intent,
            summary=self._generate_summary(),
        )

        # Print summary
        self._print_summary(result)

        return result

    def _generate_summary(self) -> str:
        """Generate a text summary of the evaluation"""
        lines = []

        passed = sum(1 for r in self.results if r.score.percentage >= 75)
        failed = len(self.results) - passed

        lines.append(f"Passed: {passed}/{len(self.results)} ({passed/len(self.results)*100:.0f}%)")
        lines.append(f"Failed: {failed}/{len(self.results)}")

        # Top issues
        low_scores = sorted(self.results, key=lambda r: r.score.total_score)[:5]
        if low_scores:
            lines.append("\nLowest Scoring Questions:")
            for r in low_scores:
                lines.append(f"  - [{r.question.id}] {r.score.total_score:.0f}%: {r.question.question[:40]}")

        return "\n".join(lines)

    def _print_summary(self, result: EvaluationResult) -> None:
        """Print evaluation summary to console"""
        print(f"\n{'=' * 60}")
        print(f"EVALUATION SUMMARY")
        print(f"{'=' * 60}")
        print(f"Overall Score: {result.total_score:.0f}/{result.max_score:.0f} ({result.percentage:.1f}%)")
        print(f"Level: {result.level.value.upper()}")
        print()

        print("By Difficulty:")
        for diff, pct in sorted(result.by_difficulty.items()):
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(f"  {diff:15} [{bar}] {pct:.1f}%")
        print()

        print("By Intent:")
        for intent, pct in sorted(result.by_intent.items()):
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(f"  {intent:20} [{bar}] {pct:.1f}%")
        print()

        print(result.summary)
        print(f"\n{'=' * 60}\n")

    def save_results(self, output_path: Path) -> None:
        """Save evaluation results to JSON file"""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_questions": len(self.results),
                "total_score": sum(r.score.total_score for r in self.results),
                "percentage": sum(r.score.percentage for r in self.results) / len(self.results) if self.results else 0,
            },
            "results": [
                {
                    "question_id": r.question.id,
                    "question": r.question.question,
                    "expected_intent": r.question.intent.value,
                    "detected_intent": r.detected_intent,
                    "confidence": r.detected_confidence,
                    "score": r.score.total_score,
                    "percentage": r.score.percentage,
                    "level": r.score.level.value,
                    "tool_calls": r.tool_calls,
                    "duration_ms": r.duration_ms,
                    "error": r.error,
                    "dimensions": [
                        {
                            "dimension": d.dimension,
                            "points": d.points,
                            "max_points": d.max_points,
                            "level": d.level.value,
                            "details": d.details,
                        }
                        for d in r.score.dimensions
                    ],
                }
                for r in self.results
            ],
        }

        with open(output_path, "w") as f:
            json.dump(results_data, f, indent=2)

        print(f"Results saved to {output_path}")

    def save_audit_logs(self, output_path: Path) -> None:
        """Save all audit logs to a single file"""
        audit_logs = []
        for result in self.results:
            if result.audit_record:
                audit_logs.append(self.audit_logger.format_for_llm(result.audit_record))

        with open(output_path, "w") as f:
            f.write("\n\n".join(audit_logs))

        print(f"Audit logs saved to {output_path}")


async def main():
    """Main entry point for running evaluations"""
    parser = argparse.ArgumentParser(description="Run OS/ONS MCP Server Evaluation")
    parser.add_argument(
        "--difficulty",
        choices=["basic", "intermediate", "advanced", "all"],
        default="all",
        help="Difficulty level to test",
    )
    parser.add_argument(
        "--intent",
        choices=[i.value for i in Intent] + ["all"],
        default="all",
        help="Intent type to test",
    )
    parser.add_argument(
        "--questions",
        type=str,
        help="Comma-separated list of question IDs to test",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evaluation_results.json"),
        help="Output file for results",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output",
    )

    args = parser.parse_args()

    if not IMPORTS_AVAILABLE:
        print("Error: Required MCP components not available")
        sys.exit(1)

    harness = EvaluationHarness(verbose=args.verbose)

    # Parse arguments
    difficulty = Difficulty(args.difficulty) if args.difficulty != "all" else None
    intent = Intent(args.intent) if args.intent != "all" else None
    question_ids = args.questions.split(",") if args.questions else None

    # Run evaluation
    result = await harness.run_evaluation(
        difficulty=difficulty,
        intent=intent,
        question_ids=question_ids,
    )

    # Save results
    harness.save_results(args.output)
    harness.save_audit_logs(args.output.with_suffix(".audit.txt"))

    # Exit with appropriate code
    sys.exit(0 if result.percentage >= 60 else 1)


if __name__ == "__main__":
    asyncio.run(main())

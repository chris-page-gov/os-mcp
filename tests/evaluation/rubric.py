"""Evaluation Rubric for OS/ONS MCP Server

This module defines the scoring criteria and rubric for evaluating
the effectiveness of the MCP server in answering user queries.

Scoring Dimensions:
1. Intent Recognition (0-25 points)
2. Tool Selection (0-25 points)
3. Efficiency (0-20 points)
4. Response Quality (0-20 points)
5. Error Handling (0-10 points)

Total: 100 points per question
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
import json


class ScoreLevel(str, Enum):
    """Qualitative score levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    FAIL = "fail"


@dataclass
class DimensionScore:
    """Score for a single dimension"""
    dimension: str
    points: float
    max_points: float
    level: ScoreLevel
    details: str
    deductions: List[str] = field(default_factory=list)


@dataclass
class QuestionScore:
    """Complete score for a question"""
    question_id: str
    question_text: str
    total_score: float
    max_score: float = 100.0
    percentage: float = 0.0
    level: ScoreLevel = ScoreLevel.FAIL
    dimensions: List[DimensionScore] = field(default_factory=list)
    tool_calls: List[str] = field(default_factory=list)
    response_summary: str = ""
    audit_log: str = ""

    def __post_init__(self):
        self.percentage = (self.total_score / self.max_score) * 100
        self.level = self._calculate_level()

    def _calculate_level(self) -> ScoreLevel:
        if self.percentage >= 90:
            return ScoreLevel.EXCELLENT
        elif self.percentage >= 75:
            return ScoreLevel.GOOD
        elif self.percentage >= 60:
            return ScoreLevel.ACCEPTABLE
        elif self.percentage >= 40:
            return ScoreLevel.POOR
        else:
            return ScoreLevel.FAIL


@dataclass
class EvaluationResult:
    """Complete evaluation result for a test run"""
    timestamp: str
    total_questions: int
    total_score: float
    max_score: float
    percentage: float
    level: ScoreLevel
    question_scores: List[QuestionScore] = field(default_factory=list)
    by_difficulty: Dict[str, float] = field(default_factory=dict)
    by_intent: Dict[str, float] = field(default_factory=dict)
    summary: str = ""


class Rubric:
    """Evaluation rubric for scoring MCP server responses"""

    # Scoring weights
    INTENT_RECOGNITION_MAX = 25
    TOOL_SELECTION_MAX = 25
    EFFICIENCY_MAX = 20
    RESPONSE_QUALITY_MAX = 20
    ERROR_HANDLING_MAX = 10

    def __init__(self):
        self.dimension_weights = {
            "intent_recognition": self.INTENT_RECOGNITION_MAX,
            "tool_selection": self.TOOL_SELECTION_MAX,
            "efficiency": self.EFFICIENCY_MAX,
            "response_quality": self.RESPONSE_QUALITY_MAX,
            "error_handling": self.ERROR_HANDLING_MAX,
        }

    def score_intent_recognition(
        self,
        expected_intent: str,
        detected_intent: Optional[str],
        confidence: float = 0.0,
    ) -> DimensionScore:
        """Score intent recognition accuracy

        Criteria:
        - 25 points: Correct intent with high confidence (>0.8)
        - 20 points: Correct intent with medium confidence (0.5-0.8)
        - 15 points: Correct intent with low confidence (<0.5)
        - 10 points: Related intent (e.g., statistics vs comparison)
        - 0 points: Wrong intent
        """
        max_points = self.INTENT_RECOGNITION_MAX
        deductions = []

        if detected_intent is None:
            return DimensionScore(
                dimension="intent_recognition",
                points=0,
                max_points=max_points,
                level=ScoreLevel.FAIL,
                details="No intent detected",
                deductions=["No route_query call or intent detection"],
            )

        if detected_intent == expected_intent:
            if confidence >= 0.8:
                points = 25
                level = ScoreLevel.EXCELLENT
                details = f"Correct intent ({expected_intent}) with high confidence ({confidence:.2f})"
            elif confidence >= 0.5:
                points = 20
                level = ScoreLevel.GOOD
                details = f"Correct intent ({expected_intent}) with medium confidence ({confidence:.2f})"
                deductions.append(f"Confidence below 0.8 (-5 points)")
            else:
                points = 15
                level = ScoreLevel.ACCEPTABLE
                details = f"Correct intent ({expected_intent}) with low confidence ({confidence:.2f})"
                deductions.append(f"Low confidence (-10 points)")
        else:
            # Check for related intents
            related_pairs = [
                ("statistics", "area_comparison"),
                ("place_lookup", "boundary_fetch"),
                ("feature_search", "place_lookup"),
            ]
            is_related = any(
                (expected_intent in pair and detected_intent in pair)
                for pair in related_pairs
            )

            if is_related:
                points = 10
                level = ScoreLevel.POOR
                details = f"Related intent: expected {expected_intent}, got {detected_intent}"
                deductions.append("Wrong but related intent (-15 points)")
            else:
                points = 0
                level = ScoreLevel.FAIL
                details = f"Wrong intent: expected {expected_intent}, got {detected_intent}"
                deductions.append("Completely wrong intent")

        return DimensionScore(
            dimension="intent_recognition",
            points=points,
            max_points=max_points,
            level=level,
            details=details,
            deductions=deductions,
        )

    def score_tool_selection(
        self,
        required_tools: List[str],
        forbidden_tools: List[str],
        actual_tools: List[str],
    ) -> DimensionScore:
        """Score tool selection accuracy

        Criteria:
        - 25 points: All required tools used, no forbidden tools
        - 20 points: All required tools used, 1 forbidden tool
        - 15 points: Most required tools used (>50%)
        - 10 points: Some required tools used
        - 0 points: No required tools or multiple forbidden tools
        """
        max_points = self.TOOL_SELECTION_MAX
        deductions = []

        # Check required tools
        required_used = [t for t in required_tools if t in actual_tools]
        required_missing = [t for t in required_tools if t not in actual_tools]
        required_ratio = len(required_used) / len(required_tools) if required_tools else 1.0

        # Check forbidden tools
        forbidden_used = [t for t in forbidden_tools if t in actual_tools]

        # Calculate base score from required tools
        if required_ratio == 1.0:
            base_score = 25
        elif required_ratio >= 0.75:
            base_score = 20
            deductions.append(f"Missing tools: {required_missing} (-5 points)")
        elif required_ratio >= 0.5:
            base_score = 15
            deductions.append(f"Missing tools: {required_missing} (-10 points)")
        elif required_ratio > 0:
            base_score = 10
            deductions.append(f"Missing most required tools: {required_missing}")
        else:
            base_score = 0
            deductions.append("No required tools used")

        # Deduct for forbidden tools
        if forbidden_used:
            penalty = min(len(forbidden_used) * 5, base_score)
            base_score -= penalty
            deductions.append(f"Used forbidden tools: {forbidden_used} (-{penalty} points)")

        # Determine level
        points = max(0, base_score)
        if points >= 23:
            level = ScoreLevel.EXCELLENT
        elif points >= 18:
            level = ScoreLevel.GOOD
        elif points >= 12:
            level = ScoreLevel.ACCEPTABLE
        elif points >= 5:
            level = ScoreLevel.POOR
        else:
            level = ScoreLevel.FAIL

        details = f"Used {len(required_used)}/{len(required_tools)} required tools"
        if forbidden_used:
            details += f", {len(forbidden_used)} forbidden tools"

        return DimensionScore(
            dimension="tool_selection",
            points=points,
            max_points=max_points,
            level=level,
            details=details,
            deductions=deductions,
        )

    def score_efficiency(
        self,
        actual_tool_calls: int,
        max_expected_calls: Optional[int],
    ) -> DimensionScore:
        """Score efficiency of tool usage

        Criteria:
        - 20 points: At or below expected calls
        - 15 points: 1-2 extra calls
        - 10 points: 3-5 extra calls
        - 5 points: 6-10 extra calls
        - 0 points: More than 10 extra calls
        """
        max_points = self.EFFICIENCY_MAX
        deductions = []

        if max_expected_calls is None:
            # No expectation set, give full points if reasonable
            if actual_tool_calls <= 5:
                points = 20
                level = ScoreLevel.EXCELLENT
            elif actual_tool_calls <= 10:
                points = 15
                level = ScoreLevel.GOOD
            else:
                points = 10
                level = ScoreLevel.ACCEPTABLE
            details = f"{actual_tool_calls} tool calls (no limit set)"
        else:
            extra_calls = actual_tool_calls - max_expected_calls

            if extra_calls <= 0:
                points = 20
                level = ScoreLevel.EXCELLENT
                details = f"{actual_tool_calls} calls (within limit of {max_expected_calls})"
            elif extra_calls <= 2:
                points = 15
                level = ScoreLevel.GOOD
                details = f"{actual_tool_calls} calls ({extra_calls} over limit)"
                deductions.append(f"{extra_calls} extra calls (-5 points)")
            elif extra_calls <= 5:
                points = 10
                level = ScoreLevel.ACCEPTABLE
                details = f"{actual_tool_calls} calls ({extra_calls} over limit)"
                deductions.append(f"{extra_calls} extra calls (-10 points)")
            elif extra_calls <= 10:
                points = 5
                level = ScoreLevel.POOR
                details = f"{actual_tool_calls} calls ({extra_calls} over limit)"
                deductions.append(f"{extra_calls} extra calls (-15 points)")
            else:
                points = 0
                level = ScoreLevel.FAIL
                details = f"{actual_tool_calls} calls (way over limit of {max_expected_calls})"
                deductions.append(f"Excessive tool calls: {extra_calls} over limit")

        return DimensionScore(
            dimension="efficiency",
            points=points,
            max_points=max_points,
            level=level,
            details=details,
            deductions=deductions,
        )

    def score_response_quality(
        self,
        response: str,
        required_keywords: List[str],
        forbidden_keywords: List[str],
        expected_values: Dict[str, Any],
    ) -> DimensionScore:
        """Score response quality and accuracy

        Criteria:
        - 20 points: All required keywords, expected values, no forbidden
        - 15 points: Most required keywords (>75%), no forbidden
        - 10 points: Some required keywords (>50%)
        - 5 points: Few required keywords
        - 0 points: Forbidden keywords present or no relevant content
        """
        max_points = self.RESPONSE_QUALITY_MAX
        deductions = []

        response_lower = response.lower()

        # Check forbidden keywords first
        forbidden_found = [kw for kw in forbidden_keywords if kw.lower() in response_lower]
        if forbidden_found:
            return DimensionScore(
                dimension="response_quality",
                points=0,
                max_points=max_points,
                level=ScoreLevel.FAIL,
                details=f"Forbidden keywords found: {forbidden_found}",
                deductions=["Forbidden keywords in response"],
            )

        # Check required keywords
        required_found = [kw for kw in required_keywords if kw.lower() in response_lower]
        required_missing = [kw for kw in required_keywords if kw.lower() not in response_lower]
        keyword_ratio = len(required_found) / len(required_keywords) if required_keywords else 1.0

        # Check expected values
        values_found = 0
        values_total = len(expected_values)
        for key, expected_val in expected_values.items():
            if str(expected_val).lower() in response_lower:
                values_found += 1

        value_ratio = values_found / values_total if values_total > 0 else 1.0

        # Combined score
        combined_ratio = (keyword_ratio + value_ratio) / 2 if values_total > 0 else keyword_ratio

        if combined_ratio >= 0.9:
            points = 20
            level = ScoreLevel.EXCELLENT
        elif combined_ratio >= 0.75:
            points = 15
            level = ScoreLevel.GOOD
            if required_missing:
                deductions.append(f"Missing keywords: {required_missing}")
        elif combined_ratio >= 0.5:
            points = 10
            level = ScoreLevel.ACCEPTABLE
            deductions.append(f"Missing keywords: {required_missing}")
        elif combined_ratio > 0:
            points = 5
            level = ScoreLevel.POOR
            deductions.append(f"Most keywords missing: {required_missing}")
        else:
            points = 0
            level = ScoreLevel.FAIL
            deductions.append("No relevant content in response")

        details = f"Found {len(required_found)}/{len(required_keywords)} keywords"
        if values_total > 0:
            details += f", {values_found}/{values_total} expected values"

        return DimensionScore(
            dimension="response_quality",
            points=points,
            max_points=max_points,
            level=level,
            details=details,
            deductions=deductions,
        )

    def score_error_handling(
        self,
        had_errors: bool,
        error_messages: List[str],
        graceful_handling: bool,
    ) -> DimensionScore:
        """Score error handling quality

        Criteria:
        - 10 points: No errors OR graceful handling with helpful message
        - 7 points: Error occurred but handled gracefully
        - 5 points: Error occurred, partially handled
        - 0 points: Unhandled error or crash
        """
        max_points = self.ERROR_HANDLING_MAX
        deductions = []

        if not had_errors:
            return DimensionScore(
                dimension="error_handling",
                points=10,
                max_points=max_points,
                level=ScoreLevel.EXCELLENT,
                details="No errors occurred",
                deductions=[],
            )

        if graceful_handling:
            if any("traceback" in str(e).lower() or "exception" in str(e).lower() for e in error_messages):
                points = 5
                level = ScoreLevel.POOR
                details = "Error with stack trace exposed"
                deductions.append("Stack trace visible to user")
            else:
                points = 7
                level = ScoreLevel.GOOD
                details = "Error handled gracefully"
        else:
            points = 0
            level = ScoreLevel.FAIL
            details = "Unhandled error"
            deductions.append("Error not handled gracefully")

        return DimensionScore(
            dimension="error_handling",
            points=points,
            max_points=max_points,
            level=level,
            details=details,
            deductions=deductions,
        )

    def calculate_total_score(self, dimensions: List[DimensionScore]) -> QuestionScore:
        """Calculate total score from dimension scores"""
        total = sum(d.points for d in dimensions)
        max_total = sum(d.max_points for d in dimensions)

        return QuestionScore(
            question_id="",
            question_text="",
            total_score=total,
            max_score=max_total,
            dimensions=dimensions,
        )


# Rubric description for documentation
RUBRIC_DESCRIPTION = """
# Evaluation Rubric for OS/ONS MCP Server

## Scoring Dimensions

### 1. Intent Recognition (0-25 points)
Measures how accurately the system identifies what the user wants.

| Score | Criteria |
|-------|----------|
| 25 | Correct intent with high confidence (>0.8) |
| 20 | Correct intent with medium confidence (0.5-0.8) |
| 15 | Correct intent with low confidence (<0.5) |
| 10 | Related but incorrect intent |
| 0 | Completely wrong intent |

### 2. Tool Selection (0-25 points)
Measures whether the right tools were used.

| Score | Criteria |
|-------|----------|
| 25 | All required tools used, no forbidden tools |
| 20 | All required tools, 1 minor forbidden tool |
| 15 | Most required tools (>50%) |
| 10 | Some required tools |
| 0 | No required tools or multiple forbidden tools |

### 3. Efficiency (0-20 points)
Measures whether the task was completed without unnecessary steps.

| Score | Criteria |
|-------|----------|
| 20 | At or below expected tool calls |
| 15 | 1-2 extra calls |
| 10 | 3-5 extra calls |
| 5 | 6-10 extra calls |
| 0 | More than 10 extra calls |

### 4. Response Quality (0-20 points)
Measures the accuracy and completeness of the response.

| Score | Criteria |
|-------|----------|
| 20 | All required keywords, expected values, no forbidden |
| 15 | Most required keywords (>75%) |
| 10 | Some required keywords (>50%) |
| 5 | Few required keywords |
| 0 | Forbidden keywords or no relevant content |

### 5. Error Handling (0-10 points)
Measures how gracefully errors are handled.

| Score | Criteria |
|-------|----------|
| 10 | No errors OR graceful handling with helpful message |
| 7 | Error occurred but handled gracefully |
| 5 | Error occurred, partially handled |
| 0 | Unhandled error or crash |

## Overall Score Levels

| Level | Percentage | Description |
|-------|-----------|-------------|
| Excellent | 90-100% | Outstanding performance |
| Good | 75-89% | Solid performance with minor issues |
| Acceptable | 60-74% | Meets minimum requirements |
| Poor | 40-59% | Below expectations, needs improvement |
| Fail | 0-39% | Unacceptable performance |
"""


if __name__ == "__main__":
    print(RUBRIC_DESCRIPTION)

"""Evaluation Framework for OS/ONS MCP Server

This package provides:
- questions.py: Comprehensive test question suite
- rubric.py: Scoring rubric and criteria
- harness.py: Test execution harness
- audit.py: Audit logging for LLM-readable traces
"""

from .questions import (
    EvaluationQuestion,
    ExpectedOutcome,
    Difficulty,
    Intent,
    ALL_QUESTIONS,
    QUESTIONS_BY_ID,
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

__all__ = [
    "EvaluationQuestion",
    "ExpectedOutcome",
    "Difficulty",
    "Intent",
    "ALL_QUESTIONS",
    "QUESTIONS_BY_ID",
    "get_questions",
    "get_question_summary",
    "Rubric",
    "QuestionScore",
    "DimensionScore",
    "EvaluationResult",
    "ScoreLevel",
    "RUBRIC_DESCRIPTION",
]

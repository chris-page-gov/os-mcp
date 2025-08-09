"""Diagnostics / error-recovery oriented prompt templates."""
from typing import Dict

DIAGNOSTICS_PROMPTS: Dict[str, str] = {
    "diagnostics_recover_invalid_collection": (
        "Goal: Demonstrate recovery from INVALID_COLLECTION. Steps: 1) Attempt search_features with an invalid collection id to capture error envelope; "
        "2) Call get_workflow_context(); 3) fetch_detailed_collections for a valid collection; 4) Re-run search_features successfully."  # noqa: E501
    ),
    "diagnostics_missing_context_then_fix": (
        "Goal: Show error when skipping planning. Steps: 1) Attempt fetch_detailed_collections before planning -> expect WORKFLOW_CONTEXT_REQUIRED; "
        "2) Call get_workflow_context(); 3) Retry fetch_detailed_collections; 4) Proceed with search_features."  # noqa: E501
    ),
}

__all__ = ["DIAGNOSTICS_PROMPTS"]

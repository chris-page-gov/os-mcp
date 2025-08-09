"""Generic planning prompt templates (transport / land use agnostic)."""
from typing import Dict

PLANNING_PROMPTS: Dict[str, str] = {
    "planning_generic_workflow": (
        "Goal: Plan a multi-collection OS NGD data workflow. Steps: 1) get_workflow_context(); 2) Identify relevant collections with rationale; "
        "3) fetch_detailed_collections for chosen collections; 4) List intended search_features calls with filters; 5) Highlight potential errors & recovery."  # noqa: E501
    ),
    "planning_routing_enrichment": (
        "Goal: Plan routing restriction enrichment for a study area. Steps: 1) get_workflow_context(); 2) fetch_detailed_collections(['tn-fts-roadlink-1']); "
        "3) get_routing_data(bbox='<bbox>', build_network=True); 4) Identify attributes to enrich via get_bulk_features; 5) Summarise output format."  # noqa: E501
    ),
}

__all__ = ["PLANNING_PROMPTS"]

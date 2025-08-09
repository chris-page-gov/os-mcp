"""Routing-focused prompt templates."""
from typing import Dict

ROUTING_PROMPTS: Dict[str, str] = {
    "routing_network_build_and_summarise": (
        "Goal: Build and summarise a routing network for a bbox. Steps: 1) get_workflow_context(); 2) get_routing_data(bbox='<bbox>', build_network=True); "
        "3) Report node/edge counts, restriction types, and suggest next analyses (turn restrictions / classification mixes)."  # noqa: E501
    ),
    "routing_restriction_audit": (
        "Goal: Audit restrictions for a bbox. Steps: 1) get_workflow_context(); 2) get_routing_data(bbox='<bbox>', build_network=True); "
        "3) Extract restriction list; 4) Group by type and presence of exemptions; 5) Suggest enrichment fields from roadlink features."  # noqa: E501
    ),
}

__all__ = ["ROUTING_PROMPTS"]

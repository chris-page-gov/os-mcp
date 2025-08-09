"""Warwickshire-focused prompt templates for OS NGD workflows.

Prompts cover: planning, queryables discovery, feature search, enrichment,
linked identifiers, routing/network, diagnostics (intentional error paths),
and integrated planning examples.
"""
from typing import Dict

WARWICKSHIRE_PROMPTS: Dict[str, str] = {
    "planning_warwickshire_overview": (
        "Objective: Produce a concise planning data brief for Warwickshire (roads + land use). "
        "Steps: 1) get_workflow_context(); 2) fetch_detailed_collections for road + land use; "
        "3) Summarise key attributes; 4) Suggest next investigative searches."
    ),
    "fetch_roadlink_queryables_warwick": (
        "Goal: List road link classification fields. Steps: 1) get_workflow_context(); "
        "2) fetch_detailed_collections(['tn-fts-roadlink-1']); 3) Return table field|type|description."
    ),
    "search_cinemas_leamington": (
        "Goal: List cinema sites near Royal Leamington Spa. Steps: 1) get_workflow_context(); "
        "2) fetch_detailed_collections(['lus-fts-site-1']); 3) search_features filter oslandusetertiarygroup = 'Cinema'; "
        "Return id, optional name, centroid coords." 
    ),
    "search_rail_stations_warwick": (
        "Goal: Identify railway stations in Warwick district. Steps: 1) get_workflow_context(); "
        "2) fetch_detailed_collections(['tn-fts-railnode-1']); 3) search_features with bbox + station filter; "
        "Return id + name if present." 
    ),
    "search_primary_roads_rugby": (
        "Goal: Extract primary road links around Rugby. Steps: 1) get_workflow_context(); 2) fetch_detailed_collections(['tn-fts-roadlink-1']); "
        "3) search_features filter classification contains 'Primary' within Rugby bbox; Return id, roadnumber, length." 
    ),
    "bulk_lookup_specific_roadlinks": (
        "Goal: Enrich given road link IDs. Steps: 1) get_workflow_context(); 2) get_bulk_features(collection_id='tn-fts-roadlink-1', identifiers=[...]); "
        "3) Summarise id, roadnumber, classification." 
    ),
    "enrichment_name_resolution": (
        "Goal: For land use site IDs, retrieve names + categories. Steps: 1) get_workflow_context(); 2) get_bulk_features('lus-fts-site-1'); "
        "Return id, name, primary/secondary group fields." 
    ),
    "linked_identifiers_uprn_to_toid_example": (
        "Goal: Cross-walk from sample UPRN to TOIDs. Steps: 1) get_workflow_context(); 2) get_linked_identifiers(identifier_type='UPRN'); "
        "Summarise linked identifiers by feature_type." 
    ),
    "linked_bulk_identifiers_crosscheck": (
        "Goal: For multiple UPRNs, fetch bulk linked features ensuring at least one per input. Steps: 1) get_workflow_context(); 2) get_bulk_linked_features; "
        "Report counts per input id." 
    ),
    "route_network_build_small_bbox": (
        "Goal: Build small road network slice. Steps: 1) get_workflow_context(); 2) get_routing_data(bbox='MINX,MINY,MAXX,MAXY', build_network=True); "
        "Summarise node/edge counts + restriction flags." 
    ),
    "analyze_turn_restrictions_stratford": (
        "Goal: List turn restrictions in Stratford-upon-Avon bbox. Steps: 1) get_workflow_context(); 2) get_routing_data(bbox='STRATFORD_BBOX', build_network=True); "
        "Provide restriction type counts." 
    ),
    "diagnostic_invalid_collection": (
        "Goal: Trigger INVALID_COLLECTION to show recovery. Steps: search_features invalid collection id; observe error_code; retry valid id." 
    ),
    "diagnostic_missing_workflow_context": (
        "Goal: Demonstrate WORKFLOW_CONTEXT_REQUIRED. Steps: call fetch_detailed_collections before get_workflow_context(); then recover." 
    ),
    "planning_multi_collection_landuse_transport": (
        "Goal: Plan integrated land use + transport study. Steps: 1) get_workflow_context(); 2) fetch_detailed_collections(['lus-fts-site-1','tn-fts-roadlink-1']); "
        "3) search_features for target site types; 4) search_features for nearby primary roads; 5) Summarise spatial join approach." 
    ),
}

__all__ = ["WARWICKSHIRE_PROMPTS"]

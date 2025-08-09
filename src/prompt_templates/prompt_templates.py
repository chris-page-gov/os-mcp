from typing import Dict

PROMPT_TEMPLATES: Dict[str, str] = {
    "usrn_breakdown": (
        "Break down USRN {usrn} into its component road links for routing analysis. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' to get street details. "
        "Step 2: Use Street geometry bbox to query Road Links: GET /collections/trn-ntwk-roadlink-4/items?bbox=[street_bbox] "
        "Step 3: Filter Road Links by Street reference using properties.street_ref matching street feature ID. "
        "Step 4: For each Road Link: GET /collections/trn-ntwk-roadnode-1/items?filter=roadlink_ref='roadlink_id' "
        "Step 5: Set crs=EPSG:27700 for British National Grid coordinates. "
        "Return: Complete breakdown of USRN into constituent Road Links with node connections."
    ),
    "restriction_matching_analysis": (
        "Perform comprehensive traffic restriction matching for road network in bbox {bbox} with SPECIFIC STREET IDENTIFICATION. "
        "Step 1: Build routing network: get_routing_data(bbox='{bbox}', limit={limit}, build_network=True) "
        "Step 2: Extract restriction data from build_status.restrictions array. "
        "Step 3: For each restriction, match to road links using restrictionnetworkreference: "
        "  - networkreferenceid = Road Link UUID from trn-ntwk-roadlink-4 "
        "  - roadlinkdirection = 'In Direction' (with geometry) or 'In Opposite Direction' (against geometry) "
        "  - roadlinksequence = order for multi-link restrictions (turns) "
        "Step 4: IMMEDIATELY lookup street names: Use get_bulk_features(collection_id='trn-ntwk-roadlink-4', identifiers=[road_link_uuids]) to resolve UUIDs to actual street names (name1_text, roadclassification, roadclassificationnumber) "
        "Step 5: Analyze restriction types by actual street names: "
        "  - One Way: Apply directional constraint to specific named road "
        "  - Turn Restriction: Block movement between named streets (from street A to street B) "
        "  - Vehicle Restrictions: Apply dimension/weight limits to specific named roads "
        "  - Access Restrictions: Apply vehicle type constraints to specific named streets "
        "Step 6: Check exemptions array (e.g., 'Pedal Cycles' exempt from one-way) for each named street "
        "Step 7: Group results by street names and road classifications (A Roads, B Roads, Local Roads) "
        "Return: Complete restriction mapping showing ACTUAL STREET NAMES with their specific restrictions, directions, exemptions, and road classifications. Present results as 'Street Name (Road Class)' rather than UUIDs."
    ),
}

# Attempt to import and merge optional regional / thematic prompt extensions.
for _module_name, _symbol in [
    ("warwickshire", "WARWICKSHIRE_PROMPTS"),
    ("planning", "PLANNING_PROMPTS"),
    ("routing", "ROUTING_PROMPTS"),
    ("diagnostics", "DIAGNOSTICS_PROMPTS"),
]:
    try:  # pragma: no cover
        _mod = __import__(f"prompt_templates.{_module_name}", fromlist=[_symbol])
        _dict = getattr(_mod, _symbol)
        for _k, _v in _dict.items():
            if _k not in PROMPT_TEMPLATES:
                PROMPT_TEMPLATES[_k] = _v
    except Exception:
        continue


PROMPT_TEMPLATES = {
    # BASIC USRN ANALYSIS
    "usrn_breakdown": (
        "Break down USRN {usrn} into its component road links for routing analysis. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' to get street details. "
        "Step 2: Use Street geometry bbox to query Road Links: GET /collections/trn-ntwk-roadlink-4/items?bbox=[street_bbox] "
        "Step 3: Filter Road Links by Street reference using properties.street_ref matching street feature ID. "
        "Step 4: For each Road Link: GET /collections/trn-ntwk-roadnode-1/items?filter=roadlink_ref='{roadlink_id}' "
        "Step 5: Set crs=EPSG:27700 for British National Grid coordinates. "
        "Return: Complete breakdown of USRN into constituent Road Links with node connections."
    ),
}

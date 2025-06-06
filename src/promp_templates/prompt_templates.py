PROMPT_TEMPLATES = {
    # BASIC USRN ANALYSIS
    "usrn_breakdown": (
        "Break down USRN {usrn} into its component road links for routing analysis. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' to get street details. "
        "Step 2: Use Street geometry bbox to query Road Links: GET /collections/trn-ntwk-roadlink-4/items?bbox=[street_bbox] "
        "Step 3: Filter Road Links by Street reference using properties.street_ref matching street feature ID. "
        "Step 4: For each Road Link: GET /collections/trn-ntwk-roadnode-1/items?filter=roadlink_ref='{roadlink_id}' "
        "Step 5: Set crs=EPSG:27700 for British National Grid coordinates. "
        "Return: Complete breakdown of USRN into constituent Road Links with node connections and geometries."
    ),
    "usrn_network_connections": (
        "Find all USRNs/Streets directly connected to USRN {usrn} through the road network. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' to get base street. "
        "Step 2: GET /collections/trn-ntwk-roadlink-4/items?filter=street_ref='{street_feature_id}' for Road Links. "
        "Step 3: GET /collections/trn-ntwk-roadnode-1/items?filter=roadlink_ref IN ('{link1}','{link2}') for terminal nodes. "
        "Step 4: GET /collections/trn-ntwk-roadlink-4/items?filter=start_node IN ('{node1}','{node2}') OR end_node IN ('{node1}','{node2}') "
        "Step 5: GET /collections/trn-ntwk-street-1/items?filter=feature_id IN ('{connected_street_refs}') "
        "Step 6: GET /collections/trn-ntwk-road-1/items?filter=roadlink_ref IN ('{all_roadlinks}') for named road context. "
        "Return: Connected USRNs with connection points, shared Road Node IDs, and named road classifications."
    ),
    "usrn_named_road_analysis": (
        "Analyze which named roads include USRN {usrn} and routing implications. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' "
        "Step 2: GET /collections/trn-ntwk-roadlink-4/items?filter=street_ref='{street_id}' "
        "Step 3: GET /collections/trn-ntwk-road-1/items?filter=roadlink_ref IN ('{roadlink_ids}') "
        "Step 4: Analyze road properties for classification (A-road, M-road, B-road, etc.). "
        "Step 5: GET /collections/trn-ntwk-road-1/items?bbox=[extended_bbox]&limit=100 for route continuity. "
        "Return: Named road classification, route importance, strategic routing value, and continuity analysis."
    ),
    # ROUTING & NAVIGATION
    "route_between_usrns": (
        "Build topological route between USRN {start_usrn} and USRN {end_usrn}. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn IN ('{start_usrn}','{end_usrn}') "
        "Step 2: GET /collections/trn-ntwk-roadlink-4/items?filter=street_ref IN ('{start_street_id}','{end_street_id}') "
        "Step 3: Calculate combined bbox and GET /collections/trn-ntwk-roadnode-1/items?bbox=[route_bbox]&limit=100 "
        "Step 4: Build network graph using Road Node connections between Road Links. "
        "Step 5: GET /collections/trn-ntwk-roadjunction-1/items?bbox=[route_bbox] for complex intersections. "
        "Step 6: Apply Dijkstra's algorithm for shortest path using Road Link distances. "
        "Return: Route sequence with Road Link IDs, geometries, turn instructions, and total distance."
    ),
    "usrn_to_address_routing": (
        "Route from USRN {usrn} to specific address using {uprn} or {postcode}. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' for origin. "
        "Step 2: Use search_by_uprn('{uprn}') or search_by_post_code('{postcode}') for destination coordinates. "
        "Step 3: GET /collections/trn-ntwk-roadnode-1/items?bbox=[address_bbox]&limit=1 for nearest road access. "
        "Step 4: GET /collections/trn-ntwk-roadlink-4/items?bbox=[origin_to_dest_bbox] for route network. "
        "Step 5: Build route topology from USRN Road Links to destination Road Node. "
        "Step 6: Include final approach: GET /collections/trn-ntwk-roadlink-4/items?bbox=[dest_local_bbox] "
        "Return: Complete door-to-door route with USRN departure, navigation sequence, and address approach."
    ),
    "usrn_junction_analysis": (
        "Analyze all junctions involving USRN {usrn} for routing complexity. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' "
        "Step 2: GET /collections/trn-ntwk-roadlink-4/items?filter=street_ref='{street_id}' "
        "Step 3: GET /collections/trn-ntwk-roadnode-1/items?filter=roadlink_ref IN ('{roadlink_list}') "
        "Step 4: GET /collections/trn-ntwk-roadjunction-1/items?filter=roadnode_ref IN ('{node_list}') "
        "Step 5: Analyze junction properties: geometry complexity, turn restrictions, traffic signals. "
        "Step 6: Calculate routing difficulty scores based on junction type and turn angles. "
        "Return: Junction locations, complexity ratings, turn restrictions, and routing recommendations."
    ),
    # ACCESSIBILITY & MOBILITY
    "usrn_accessibility_analysis": (
        "Analyze accessibility routing options for USRN {usrn} including pedestrian access. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' "
        "Step 2: GET /collections/trn-ntwk-roadlink-4/items?filter=street_ref='{street_id}' with pavement attributes. "
        "Step 3: GET /collections/trn-ntwk-pavementlink-1/items?bbox=[street_bbox] for dedicated pavement data. "
        "Step 4: GET /collections/trn-ntwk-pathlink-1/items?bbox=[street_bbox]&limit=50 for pedestrian paths. "
        "Step 5: GET /collections/trn-ntwk-connectinglink-1/items?bbox=[street_bbox] for path-road connections. "
        "Step 6: Analyze presenceofstreetlight_coverage and pavement width/presence attributes. "
        "Return: Accessibility report with pavement widths, lighting coverage, path connections, and mobility ratings."
    ),
    "usrn_path_integration": (
        "Find pedestrian/cycle path integration points for USRN {usrn}. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' "
        "Step 2: GET /collections/trn-ntwk-pathlink-1/items?bbox=[street_bbox]&limit=100 "
        "Step 3: GET /collections/trn-ntwk-pathlink-2/items?bbox=[street_bbox]&limit=100 "
        "Step 4: GET /collections/trn-ntwk-connectinglink-1/items?bbox=[street_bbox] "
        "Step 5: GET /collections/trn-ntwk-connectingnode-1/items?bbox=[street_bbox] "
        "Step 6: GET /collections/trn-ntwk-path-1/items using Path-PathLink reference table for named paths. "
        "Return: All pedestrian/cycle access points, path network connections, and named route options."
    ),
    "cycling_routing_usrn": (
        "Plan cycling routes involving USRN {usrn}. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' "
        "Step 2: GET /collections/trn-ntwk-roadlink-4/items?filter=street_ref='{street_id}' AND road_type NOT IN ('Motorway','Trunk Road') "
        "Step 3: GET /collections/trn-ntwk-pathlink-1/items?bbox=[area_bbox] for dedicated cycle paths. "
        "Step 4: GET /collections/trn-ntwk-pathlink-2/items?bbox=[area_bbox] for additional cycling infrastructure. "
        "Step 5: Analyze road surface, traffic classification, and gradient from Road Link properties. "
        "Step 6: Connect via GET /collections/trn-ntwk-connectinglink-1/items for off-road transitions. "
        "Return: Cycling route options with surface quality, traffic levels, gradients, and off-road connections."
    ),
    # MULTIMODAL TRANSPORT
    "usrn_multimodal_access": (
        "Find all transport access points for USRN {usrn} including roads, paths, rail, and ferry. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' for primary road access. "
        "Step 2: GET /collections/trn-ntwk-pathlink-1/items?bbox=[area_bbox]&limit=100 for pedestrian network. "
        "Step 3: GET /collections/trn-ntwk-railwaylink-1/items?bbox=[area_bbox]&limit=50 for rail connections. "
        "Step 4: GET /collections/trn-ntwk-ferrylink-1/items?bbox=[area_bbox] for water transport. "
        "Step 5: GET /collections/trn-ntwk-ferryterminal-1/items?bbox=[area_bbox] for ferry terminals. "
        "Step 6: GET /collections/trn-ntwk-railwaylinkset-1/items and use Railway Linkset reference for named lines. "
        "Step 7: GET /collections/trn-ntwk-connectinglink-1/items for intermodal connection points. "
        "Return: Comprehensive multimodal access with rail stations, ferry terminals, path networks, and transfer points."
    ),
    "usrn_rail_connections": (
        "Find railway connections near USRN {usrn}. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' for location. "
        "Step 2: Calculate 1km buffer bbox and GET /collections/trn-ntwk-railwaylink-1/items?bbox=[buffer_bbox] "
        "Step 3: GET /collections/trn-ntwk-railwaynode-1/items?bbox=[buffer_bbox] for stations and junctions. "
        "Step 4: GET /collections/trn-ntwk-railwaylinkset-1/items for named railway lines using reference table. "
        "Step 5: Filter Railway Nodes by type='Station' for passenger access points. "
        "Step 6: Calculate walking distance from USRN to each station via road network. "
        "Return: Railway access analysis with station names, distances, rail line names, and walking routes."
    ),
    "usrn_tram_analysis": (
        "Analyze tram connections and presence for USRN {usrn}. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' "
        "Step 2: GET /collections/trn-ntwk-roadlink-4/items?filter=street_ref='{street_id}' "
        "Step 3: Check presenceoftram_extentoflink attribute for each Road Link (Full/Partial/None). "
        "Step 4: GET /collections/trn-ntwk-tramonroad-1/items?bbox=[street_bbox] for dedicated tram features. "
        "Step 5: Analyze tram coverage extent and integration with road network. "
        "Step 6: Find tram stops and interchanges within area. "
        "Return: Tram presence analysis, coverage extent, integration points, and multimodal opportunities."
    ),
    # NETWORK ANALYSIS
    "build_usrn_network_graph": (
        "Build complete routing network graph centered on USRN {usrn}. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' for center point. "
        "Step 2: Calculate analysis radius (e.g., 2km) and GET /collections/trn-ntwk-roadlink-4/items?bbox=[analysis_bbox]&limit=500 "
        "Step 3: GET /collections/trn-ntwk-roadnode-1/items?bbox=[analysis_bbox]&limit=1000 for network vertices. "
        "Step 4: GET /collections/trn-ntwk-pathlink-1/items?bbox=[analysis_bbox] for pedestrian network. "
        "Step 5: GET /collections/trn-ntwk-roadjunction-1/items?bbox=[analysis_bbox] for junction complexity weights. "
        "Step 6: Build graph: nodes=Road Nodes, edges=Road Links, weights=distance+junction_complexity. "
        "Step 7: Add multimodal edges for rail/ferry/tram connections within area. "
        "Return: Complete routing graph with nodes, weighted edges, multimodal connections, and network statistics."
    ),
    "usrn_road_link_analysis": (
        "Detailed analysis of individual Road Links within USRN {usrn}. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' "
        "Step 2: GET /collections/trn-ntwk-roadlink-4/items?filter=street_ref='{street_id}' "
        "Step 3: For each Road Link, extract: geometry, start_node, end_node, length, surface_type. "
        "Step 4: Analyze pavement attributes: width_left, width_right, presence_left, presence_right. "
        "Step 5: Check presenceoftram_extentoflink and presenceofstreetlight_coverage attributes. "
        "Step 6: GET /collections/trn-ntwk-roadnode-1/items for start/end node details and connections. "
        "Step 7: Calculate directional bearing and junction angles. "
        "Return: Comprehensive Road Link analysis with infrastructure details, connectivity, and geometric properties."
    ),
    # EMERGENCY & SPECIALIZED ROUTING
    "emergency_services_routing": (
        "Plan emergency services routing involving USRN {usrn} with multiple access points. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' "
        "Step 2: GET /collections/trn-ntwk-roadlink-4/items?filter=street_ref='{street_id}' "
        "Step 3: Identify all Road Nodes for primary and alternative access routes. "
        "Step 4: GET /collections/trn-ntwk-roadlink-4/items?bbox=[emergency_area_bbox] for surrounding network. "
        "Step 5: Filter by road_width >= emergency_vehicle_width and surface_type suitable for heavy vehicles. "
        "Step 6: GET /collections/trn-ntwk-pathlink-1/items for emergency pedestrian access routes. "
        "Step 7: Check trn-rami-restriction-1 for any access restrictions or weight limits. "
        "Step 8: Plan multiple approach routes with alternative paths for service redundancy. "
        "Return: Emergency access plan with primary/secondary routes, vehicle suitability, and pedestrian access options."
    ),
    "freight_routing_usrn": (
        "Plan freight/HGV routing for USRN {usrn}. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' "
        "Step 2: GET /collections/trn-ntwk-roadlink-4/items?filter=street_ref='{street_id}' "
        "Step 3: Check Road Link attributes: road_width, surface_type, gradient, weight_restriction. "
        "Step 4: GET /collections/trn-rami-restriction-1/items?bbox=[area_bbox] for HGV restrictions. "
        "Step 5: Analyze turning circles at junctions: GET /collections/trn-ntwk-roadjunction-1/items "
        "Step 6: Identify loading bay access and delivery constraints. "
        "Step 7: Avoid: residential streets with width < 6m, weight limits < vehicle_weight, height restrictions. "
        "Return: HGV-suitable routing with restrictions, loading access, turning capabilities, and delivery constraints."
    ),
    "usrn_traffic_optimization": (
        "Plan traffic-optimized routes involving USRN {usrn}. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' "
        "Step 2: GET /collections/trn-rami-averageandindicativespeed-1/items?bbox=[area_bbox] for speed data. "
        "Step 3: GET /collections/trn-rami-restriction-1/items?bbox=[area_bbox] for traffic restrictions. "
        "Step 4: GET /collections/trn-ntwk-roadlink-4/items with traffic classification and capacity attributes. "
        "Step 5: GET /collections/trn-ntwk-roadjunction-1/items for bottleneck analysis and signal timing. "
        "Step 6: Calculate time-based routing: travel_time = distance / average_speed + junction_delay. "
        "Step 7: Apply rush-hour modifiers and restriction penalties to edge weights. "
        "Return: Time-optimized route with speed profiles, estimated travel times, traffic restrictions, and delay predictions."
    ),
    # SPATIAL ANALYSIS
    "usrn_spatial_analysis": (
        "Perform comprehensive spatial analysis around USRN {usrn} within {radius}m. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' to get center coordinates. "
        "Step 2: Calculate bbox = [x-{radius}, y-{radius}, x+{radius}, y+{radius}] in EPSG:27700. "
        "Step 3: GET /collections/trn-ntwk-roadlink-4/items?bbox=[bbox]&limit=200&crs=EPSG:27700 "
        "Step 4: GET /collections/trn-ntwk-pathlink-1/items?bbox=[bbox]&limit=100 for pedestrian infrastructure. "
        "Step 5: GET /collections/trn-ntwk-railwaylink-1/items?bbox=[bbox] for rail network analysis. "
        "Step 6: GET /collections/trn-fts-streetlight-1/items?bbox=[bbox] for lighting infrastructure. "
        "Step 7: Calculate network density, connectivity metrics, and accessibility scores. "
        "Return: Spatial analysis report with infrastructure density, connectivity metrics, and accessibility assessment."
    ),
    "usrn_compound_structure_analysis": (
        "Find compound structures affecting USRN {usrn} routing. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn='{usrn}' "
        "Step 2: GET /collections/str-fts-compoundstructure-1/items?bbox=[street_bbox] "
        "Step 3: Filter by networkover='Road' OR networkunder='Road' for road-relevant structures. "
        "Step 4: Analyze bridge/tunnel constraints: height restrictions, width limitations. "
        "Step 5: Check for alternative routes if structure has access restrictions. "
        "Return: Structure locations, network intersections, routing constraints, and alternative paths."
    ),
    "route_compound_structures_analysis": (
        "Find all compound structures along the route from USRN {start_usrn} to USRN {end_usrn}. "
        "Step 1: GET /collections/trn-ntwk-street-1/items?filter=usrn IN ('{start_usrn}','{end_usrn}') "
        "Step 2: GET /collections/trn-ntwk-roadlink-4/items?filter=street_ref IN ('{start_street_id}','{end_street_id}') "
        "Step 3: Build route network between USRNs using Road Node connections and shortest path algorithm. "
        "Step 4: Create route corridor: buffer route geometry by 100m to capture nearby structures. "
        "Step 5: GET /collections/str-fts-compoundstructure-1/items?bbox=[route_corridor_bbox]&limit=200 "
        "Step 6: GET /collections/str-fts-compoundstructure-2/items?bbox=[route_corridor_bbox]&limit=200 "
        "Step 7: Filter compound structures where networkover='Road' OR networkunder='Road' OR description IN ('Bridge','Viaduct','Underpass','Tunnel'). "
        "Step 8: For each structure, check spatial intersection with route geometry using INTERSECTS(route_geom, structure_geom). "
        "Step 9: Analyze routing impact: bridges (height clearance), tunnels (width/height restrictions), underpasses (vehicle restrictions). "
        "Step 10: Sort structures by distance along route from start to end. "
        "Return: Ordered list of compound structures along route with descriptions, network interactions, routing constraints, and GPS coordinates."
    ),
    "route_bridge_tunnel_analysis": (
        "Analyze bridges and tunnels specifically along route from USRN {start_usrn} to USRN {end_usrn}. "
        "Step 1: Build route geometry using route_between_usrns template. "
        "Step 2: GET /collections/str-fts-compoundstructure-1/items?bbox=[route_bbox] "
        "Step 3: Filter by description IN ('Bridge','Footbridge','Viaduct','Road Bridge','Rail Bridge','Aqueduct','Tunnel','Underpass','Subway'). "
        "Step 4: For bridges: check if networkover='Road' (you go over) or networkunder='Road' (you go under). "
        "Step 5: For tunnels: check if networkover contains surface features and networkunder='Road' (you go through). "
        "Step 6: Analyze routing constraints: "
        "   - Bridges: height restrictions for vehicles going under "
        "   - Tunnels: width/height clearances, emergency access "
        "   - Underpasses: vehicle size limitations "
        "Step 7: Calculate structure locations as distance/bearing from route start. "
        "Return: Bridge/tunnel inventory with clearances, restrictions, alternative routes if needed."
    ),
    "route_infrastructure_obstacles": (
        "Identify all infrastructure obstacles and restrictions along route from USRN {start_usrn} to USRN {end_usrn}. "
        "Step 1: Build complete route geometry using Road Links and Road Nodes. "
        "Step 2: Create 200m buffer corridor around route centerline. "
        "Step 3: GET /collections/str-fts-compoundstructure-1/items?bbox=[corridor_bbox] for major structures. "
        "Step 4: GET /collections/trn-rami-restriction-1/items?bbox=[corridor_bbox] for traffic restrictions. "
        "Step 5: GET /collections/trn-rami-routinghazard-1/items?bbox=[corridor_bbox] for routing hazards. "
        "Step 6: Filter compound structures by spatial intersection with route geometry. "
        "Step 7: Categorize obstacles: "
        "   - Height restrictions: bridges with low clearance "
        "   - Width restrictions: narrow tunnels, underpasses "
        "   - Weight restrictions: from RAMI restriction data "
        "   - Access restrictions: private bridges, toll structures "
        "Step 8: Calculate detour routes for restricted vehicles around each obstacle. "
        "Return: Complete obstacle inventory with restriction details and alternative routing options."
    ),
    "route_multimodal_crossings": (
        "Find all multimodal transport crossings along route from USRN {start_usrn} to USRN {end_usrn}. "
        "Step 1: Build route geometry between USRNs. "
        "Step 2: GET /collections/str-fts-compoundstructure-1/items?bbox=[route_bbox] "
        "Step 3: Filter by networkover IN ('Railway','Canal','Water','Multiple') OR networkunder IN ('Railway','Canal','Water','Multiple'). "
        "Step 4: Identify crossing types: "
        "   - Road over rail: bridges where networkover='Road' AND networkunder='Railway' "
        "   - Road under rail: tunnels/underpasses where networkover='Railway' AND networkunder='Road' "
        "   - Water crossings: bridges where networkunder='Water' or networkunder='Canal' "
        "   - Complex crossings: where networkover='Multiple' or networkunder='Multiple' "
        "Step 5: GET /collections/trn-ntwk-railwaylink-1/items?bbox=[route_bbox] to identify rail lines. "
        "Step 6: GET /collections/wtr-ntwk-waterlink-1/items?bbox=[route_bbox] to identify water features. "
        "Step 7: Calculate crossing safety ratings and alternative routes. "
        "Return: All transport mode crossings with safety analysis and routing alternatives."
    ),
    "freight_route_structure_clearances": (
        "Analyze compound structure clearances for freight routing from USRN {start_usrn} to USRN {end_usrn}. "
        "Step 1: Build freight-suitable route using Road Links with width >= 6m. "
        "Step 2: GET /collections/str-fts-compoundstructure-1/items?bbox=[route_bbox] "
        "Step 3: Filter structures affecting freight: bridges (height), tunnels (width/height), underpasses (clearance). "
        "Step 4: Check description for 'Bridge', 'Viaduct', 'Underpass', 'Tunnel' with networkunder='Road'. "
        "Step 5: Analyze clearance constraints for: "
        "   - Height: bridges over road (typical 4.9m minimum for HGV) "
        "   - Width: tunnel/underpass openings (3.5m+ for HGV) "
        "   - Weight: structural load limits from compound structure data "
        "Step 6: Cross-reference with trn-rami-restriction-1 for HGV weight/size limits. "
        "Step 7: Plan alternative routes for structures with insufficient clearances. "
        "Return: Freight-specific clearance analysis with compliant routes and restriction details."
    ),
    "uprn_to_road_infrastructure": (
        "Step 1: Use get_linked_identifiers('UPRN', '{uprn}', 'RoadLink') to find road access"
        "Step 2: Use get_linked_identifiers('UPRN', '{uprn}', 'TopographicArea') for building footprint"
        "Step 3: Cross-reference with your existing USRN analysis templates"
    ),
}

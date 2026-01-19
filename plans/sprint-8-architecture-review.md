# Sprint 8: Architecture Review & Redesign

## Executive Summary

The current architecture has grown organically from Sprint 1-7, adding features incrementally. Now that we have MCP-Apps, Skills documentation, and Tool Search, we need a **root-and-branch review** to ensure the architecture serves users effectively.

**The Birmingham Problem** exemplifies what's wrong: a simple "find Birmingham" query triggers a complex 50-step workflow when a single tool call would suffice.

## Current Architecture Problems

### Problem 1: Tool Overload Without Routing
- **37 tools** with no intelligent routing
- Claude sees tools in arbitrary order and picks based on description matching
- No "front door" that understands intent and routes appropriately

### Problem 2: Competing Data Sources Without Clear Boundaries
| Source | Purpose | When to Use |
|--------|---------|-------------|
| ONS Geography API | Administrative areas (councils, wards) | "Find Birmingham", "Where is Manchester" |
| ONS Statistics API | Government statistics | "Wellbeing in Coventry", "House prices" |
| OS NGD API | Mapping features (buildings, roads) | "Find cinemas", "Show buildings" |

**Problem**: Nothing tells Claude which source to use. It defaults to OS NGD because those tools are more prominent.

### Problem 3: The 2-Step Workflow is Overused
The OS NGD workflow (`os_ngd_init_mapping_workflow` → `fetch_detailed_collections` → `search_features`) is:
- Required for complex mapping queries
- Completely unnecessary for simple lookups
- But it's presented as THE way to do things

### Problem 4: Tool Descriptions Are Implementation-Focused
Current: "Initialize workflow context with available collections"
Should be: "Start here ONLY if you need detailed mapping data (buildings, roads, land use)"

### Problem 5: No Intent Classification Layer
Other successful MCP implementations have a "router" that:
1. Understands the user's intent
2. Routes to the appropriate subsystem
3. Returns consolidated results

## Proposed New Architecture

### Option A: Smart Router Tool (Recommended)

```
┌─────────────────────────────────────────────────────────┐
│                    User Query                            │
│              "Find Birmingham"                           │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              route_query (ALWAYS FIRST)                  │
│  Classifies intent and returns recommended tool path     │
│                                                          │
│  Input: "Find Birmingham"                                │
│  Output: {                                               │
│    "intent": "place_lookup",                             │
│    "recommended_tool": "search_geographic_areas",        │
│    "parameters": {"query": "Birmingham", "level": "local_auth"}, │
│    "confidence": 0.95                                    │
│  }                                                       │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│           search_geographic_areas                        │
│           (Single tool call, done)                       │
└─────────────────────────────────────────────────────────┘
```

### Option B: Unified Query Tool

```
┌─────────────────────────────────────────────────────────┐
│              smart_query (SINGLE ENTRY POINT)            │
│                                                          │
│  Handles all common queries internally:                  │
│  - Place lookups → ONS Geography                         │
│  - Statistics → ONS Statistics                           │
│  - Feature searches → OS NGD (with auto-init)            │
│                                                          │
│  Input: "Find Birmingham"                                │
│  Output: {                                               │
│    "type": "place",                                      │
│    "results": [{code: "E08000025", name: "Birmingham"}]  │
│  }                                                       │
└─────────────────────────────────────────────────────────┘
```

### Option C: Tiered Tool Categories (Current + Improvements)

Keep current tools but:
1. Add a **prominent query classifier** that's ALWAYS called first
2. Rename tools to include intent (e.g., `place_lookup`, `mapping_search`, `statistics_query`)
3. Add clear "YOU ARE HERE" guidance in every tool description

## Recommended Implementation: Option A + Option C Hybrid

### Phase 1: Add Query Router Tool

Create `route_query` tool that:
- Is ALWAYS loaded and prominently described
- Takes natural language query
- Returns intent classification + recommended tool + parameters
- Becomes the "front door" for all queries

### Phase 2: Simplify Tool Categories

Reduce from 37 tools to clear tiers:

**Tier 1: Entry Points (ALWAYS LOADED)**
```
route_query           - "Start here. Classifies your query and recommends the right tool"
search_geographic_areas - "Find UK places by name (cities, towns, councils)"
list_ons_datasets     - "Browse available statistics datasets"
select_geographic_area - "Open interactive map for area selection"
```

**Tier 2: Data Retrieval (AUTO-DISCOVERED)**
```
get_statistics        - "Get statistics for known area codes"
fetch_boundaries      - "Get GeoJSON boundaries for known area codes"
compare_areas         - "Compare statistics across areas"
```

**Tier 3: Advanced Features (DEFERRED)**
```
os_ngd_init_mapping_workflow  - "For OS NGD mapping features ONLY"
fetch_detailed_collections
search_features
...
```

### Phase 3: Improve Tool Descriptions

Every tool description must answer:
1. **WHAT** does this tool do?
2. **WHEN** should I use it?
3. **WHEN NOT** to use it?
4. **EXAMPLE** query that triggers this tool

### Phase 4: Add Workflow Templates

Pre-built workflows for common patterns:
```python
WORKFLOWS = {
    "find_place": ["route_query", "search_geographic_areas"],
    "get_statistics": ["route_query", "search_geographic_areas", "get_statistics"],
    "find_features": ["route_query", "os_ngd_init_mapping_workflow", "fetch_detailed_collections", "search_features"],
    "compare_areas": ["route_query", "search_geographic_areas", "compare_areas"],
}
```

## Sprint 8 Tasks

### Week 1: Analysis & Design

| Task | Description | Status |
|------|-------------|--------|
| 8.1.1 | Audit all 37 tools for purpose clarity | Pending |
| 8.1.2 | Categorize tools into intent groups | Pending |
| 8.1.3 | Design route_query tool specification | Pending |
| 8.1.4 | Create decision flowchart for tool selection | Pending |
| 8.1.5 | Review MCP-Apps integration points | Pending |

### Week 2: Implementation

| Task | Description | Status |
|------|-------------|--------|
| 8.2.1 | Implement route_query tool | Pending |
| 8.2.2 | Update tool loading tiers | Pending |
| 8.2.3 | Rewrite tool descriptions | Pending |
| 8.2.4 | Add workflow templates | Pending |
| 8.2.5 | Update SKILL.md with new architecture | Pending |

### Week 3: Testing & Polish

| Task | Description | Status |
|------|-------------|--------|
| 8.3.1 | Test "Find Birmingham" scenario | Pending |
| 8.3.2 | Test statistics workflow | Pending |
| 8.3.3 | Test feature search workflow | Pending |
| 8.3.4 | Performance testing | Pending |
| 8.3.5 | Documentation update | Pending |

## Success Criteria

1. **"Find Birmingham"** works in 1-2 tool calls (not 10+)
2. **Tool selection accuracy** > 90% on common queries
3. **No workflow context errors** for simple lookups
4. **Clear documentation** showing which tool for which intent

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing workflows | High | Maintain backward compatibility, add new tools rather than remove |
| Over-engineering | Medium | Start with route_query only, iterate |
| LLM ignoring routing | Medium | Make route_query output mandatory context for next call |

## Files to Modify

1. `src/mcp_service/os_service.py` - Add route_query tool
2. `src/mcp_service/tool_search_config.py` - Reorganize tiers
3. `src/tools/query_router.py` - New routing logic
4. `SKILL.md` - Rewrite with new architecture
5. `docs/tutorial.md` - Update with new patterns
6. `README.md` - Update architecture description

## Open Questions

1. Should `route_query` be mandatory (always called first) or advisory?
2. Should we create a `smart_query` unified tool or keep tools separate?
3. How do we handle widget interactions with the new routing?
4. Should we deprecate the 2-step workflow for simple cases?

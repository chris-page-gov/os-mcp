# MCP-Apps Implementation Progress

This document tracks progress through the [Implementation Roadmap](on-ons%20mcp%20implementation-roadmap.md).

**Last Updated**: 2026-01-19

## Overall Status

| Metric | Value |
|--------|-------|
| Current Sprint | 8 Complete - Architecture Review & Evaluation |
| Tools Added | 16 (15 MCP-Apps + 1 route_query) |
| Total Tools | 38 (6 always-loaded, 32 deferred) |
| UI Resources Added | 4 (geography-selector, statistics-dashboard, feature-inspector, route-planner) |
| Test Count | 370+ passing |
| Coverage | >80% |
| Prompt Templates | 13 new MCP-Apps prompts added |
| Tool Search | 6 always-loaded (route_query, search_geographic_areas, select_geographic_area, get_statistics, hello_world, version_info), 32 deferred |
| Documentation | User tutorial (docs/tutorial.md), Sprint 8 plan |

## Recent Updates

- ONS API client now raises `ONSAPIError` for connection failures and requires async context manager usage.
- Test assertions updated for HTTP middleware detection and MCP tool search prompt checks.

---

## Internal Notes

- 2026-01-17: Added `.github/copilot-instructions.md` to capture repo-specific AI agent conventions.

## Sprint 1: MCP-Apps Foundation ✅ COMPLETE

**Goal**: Get basic MCP-Apps infrastructure working with a minimal geography selector.

### Tasks

| Task | Status | Notes |
|------|--------|-------|
| 1.1 Directory structure | ✅ Done | Created `src/ui/`, `src/tools/`, `src/clients/` |
| 1.2 UI resource registration | ✅ Done | `src/mcp_service/ui_resources.py` with 3 resources |
| 1.3 Geography tools | ✅ Done | `src/tools/geography_tools.py` with 3 tools |
| 1.4 Basic widget HTML | ✅ Done | `src/ui/geography_selector.html` (~700 lines) |
| 1.5 Integration with OSDataHubService | ✅ Done | Tools registered, skip workflow context |
| 1.6 Unit tests | ✅ Done | 14 tests in `tests/test_geography_tools.py` |

### Files Created
- `src/ui/__init__.py`
- `src/tools/__init__.py`
- `src/clients/__init__.py`
- `src/mcp_service/ui_resources.py`
- `src/tools/geography_tools.py`
- `src/ui/geography_selector.html`
- `tests/test_geography_tools.py`

### Files Modified
- `src/mcp_service/os_service.py` - Added imports, tool methods, registration

---

## Sprint 2: Selection Flow & Multi-level Support ✅ COMPLETE

**Goal**: Complete widget functionality with postcode search and verified ONS API integration.

### Tasks

| Task | Status | Notes |
|------|--------|-------|
| 2.1 Postcode search | ✅ Done | Using postcodes.io API |
| 2.2 ONS API service name verification | ✅ Done | Updated to December 2024 services |
| 2.3 Live API testing | ✅ Done | Birmingham search, Coventry boundary fetch working |
| 2.4 Widget polish | ✅ Done | Multi-select, level switching, search |
| 2.5 Documentation | ✅ Done | CLAUDE.md, CHANGELOG.md, README.md updated |

### API Verification
ONS ArcGIS REST services verified (January 2025):
- `Local_Authority_Districts_December_2024_Boundaries_UK_BFC`
- `Westminster_Parliamentary_Constituencies_July_2024_Boundaries_UK_BFC`
- `Wards_December_2024_Boundaries_UK_BFC`
- `Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BFC_V10`
- `Middle_layer_Super_Output_Areas_December_2021_Boundaries_EW_BFC_V7`
- `Output_Areas_2021_EW_BFC_V8`

---

## Sprint 3: ONS Statistics Integration ✅ COMPLETE

**Goal**: Add ONS statistics API client and basic statistics tools.

### ONS API Research Findings (January 2025)

| Property | Value |
|----------|-------|
| Base URL | `https://api.beta.ons.gov.uk/v1` |
| Authentication | None required (open API) |
| Rate Limits | 120 req/10s, 200 req/min |
| Total Datasets | 337 |
| Census 2021 Datasets | 30+ (via `?is_based_on=UR`) |
| V0 API Status | Retired November 2024 |

**Data Structure**: Datasets → Editions → Versions → Dimensions → Observations

**Key Discovery**: ONS observations API requires ALL dimensions to be specified, with only ONE dimension allowed to use the `*` wildcard.

**Key Local Authority Datasets**:
- `wellbeing-local-authority` - Personal well-being estimates
- `house-prices-local-authority` - House price statistics
- `gdp-by-local-authority` - GDP data
- `life-expectancy-by-local-authority` - Life expectancy
- `mid-year-pop-est` - Population estimates
- `weekly-deaths-local-authority` - Death statistics

**Census 2021 Datasets** (TS-series):
- `TS067` - Highest level of qualification
- `TS063` - Occupation
- `TS062` - NS-SEC (socio-economic classification)
- `TS061` - Method used to travel to work
- `TS060` - Industry

### Tasks

| Task | Status | Notes |
|------|--------|-------|
| 3.1 ONS Statistics API research | ✅ Done | V1 API, no auth, 337 datasets |
| 3.2 Create `src/clients/ons_client.py` | ✅ Done | API client with rate limiting and caching |
| 3.3 Statistics tools | ✅ Done | 4 tools: list_ons_datasets, get_dataset_info, get_statistics, compare_areas |
| 3.4 Caching layer | ✅ Done | TTL-based cache in ONSCache class |
| 3.5 Tests | ✅ Done | 42 tests in test_statistics_tools.py and test_ons_client.py |

### Files Created
- `src/clients/ons_client.py` - ONS Statistics API client (~480 lines)
- `src/tools/statistics_tools.py` - 4 MCP tools (~530 lines)
- `tests/test_statistics_tools.py` - 23 tests
- `tests/test_ons_client.py` - 19 tests

### Files Modified
- `src/mcp_service/os_service.py` - Added statistics tool imports and registration

---

## Sprint 4: Statistics Dashboard Widget ✅ COMPLETE

**Goal**: Interactive dashboard for visualizing ONS statistics.

### Tasks

| Task | Status | Notes |
|------|--------|-------|
| 4.1 Dashboard HTML scaffold | ✅ Done | Self-contained HTML with embedded CSS/JS |
| 4.2 Chart components | ✅ Done | Chart.js integration with line and bar charts |
| 4.3 Data binding | ✅ Done | MCP data injection via window.__MCP_DATA__ |
| 4.4 Area comparison | ✅ Done | Multi-area comparison table and charts |
| 4.5 Export functionality | ✅ Done | CSV, JSON, and clipboard export |

### Files Created
- `src/ui/statistics_dashboard.html` (~600 lines)

### Features Implemented
- **Summary Cards**: Latest value, average, and range statistics
- **Time Series Charts**: Line and bar chart options with Chart.js
- **Area Comparison**: Side-by-side comparison table with rankings
- **Data Table**: Full observation data display
- **Export Options**: CSV, JSON, and copy-to-clipboard
- **Responsive Design**: Mobile-friendly layout

---

## Sprint 5: Enhanced Features ✅ COMPLETE

**Goal**: Feature inspector, route planner integration, and cross-widget communication.

### Tasks

| Task | Status | Notes |
|------|--------|-------|
| 5.1 Feature inspector widget | ✅ Done | Full widget with properties, map, linked identifiers, export |
| 5.2 Linked identifiers display | ✅ Done | Tabbed navigation (TOID, UPRN, USRN), click-to-navigate |
| 5.3 Route planner integration | ✅ Done | Map-based selection, waypoints, directions display |
| 5.4 Cross-widget communication | ✅ Done | Shared context, selection sharing between widgets |

### Files Created
- `src/ui/feature_inspector.html` - Feature inspector widget (~650 lines)
- `src/ui/route_planner.html` - Route planner widget (~550 lines)
- `src/tools/feature_inspector_tools.py` - 2 tools + helper functions
- `src/tools/route_planner_tools.py` - 2 tools + helper functions
- `src/tools/widget_communication.py` - 3 cross-widget tools + SharedContext
- `tests/test_feature_inspector_tools.py` - 25 unit tests
- `tests/test_route_planner_tools.py` - 24 unit tests
- `tests/test_widget_communication.py` - 21 unit tests

### Files Modified
- `src/mcp_service/os_service.py` - Added 7 new tool methods and registrations
- `src/mcp_service/ui_resources.py` - Added route-planner resource registration

### New Tools (Sprint 5)
| Tool | Description |
|------|-------------|
| `inspect_feature` | Opens feature inspector widget with UI resource reference |
| `get_feature_with_linked` | Prepares feature data with linked identifiers |
| `plan_route` | Opens route planner widget with start/end configuration |
| `get_route_network` | Gets road network data for a bounding box |
| `get_shared_context` | Gets current cross-widget shared state |
| `update_shared_context` | Adds/removes/clears selections in shared context |
| `share_selection` | Shares selection from one widget to another |

### New UI Resources (Sprint 5)
| URI | Description |
|-----|-------------|
| `ui://os-ons/feature-inspector` | Interactive feature detail view with map and linked IDs |
| `ui://os-ons/route-planner` | Interactive route planning with waypoints and directions |

---

## Sprint 6: Polish & Release ✅ COMPLETE

**Goal**: Production readiness with comprehensive testing and documentation.

### Tasks

| Task | Status | Notes |
|------|--------|-------|
| 6.1 Test coverage >80% | ✅ Done | 73% → 80%+ (320+ tests, 12 new test files) |
| 6.2 Documentation complete | ✅ Done | SKILL.md, user guide, prompt templates |
| 6.3 Performance testing | ✅ Done | test_performance.py with boundary/cache tests |
| 6.4 Error handling audit | ✅ Done | All tools use ErrorCode envelopes |
| 6.5 Production deployment | ✅ Done | Multi-stage Docker, CI/CD with coverage |

### Files Created (Sprint 6)

**Documentation:**
- `SKILL.md` - Comprehensive skills documentation for LLM context
- `docs/mcp_apps_guide.md` - User guide for MCP-Apps widgets
- `src/prompt_templates/mcp_apps.py` - 13 new MCP-Apps workflow prompts

**Test Files (for coverage improvement):**
- `tests/test_routing_service_detailed.py` - 40+ tests for InMemoryRoutingNetwork and OSRoutingService
- `tests/test_ui_resources.py` - 15+ tests for OSUIResources and widget loading
- `tests/test_guardrails.py` - 15+ tests for prompt injection detection
- `tests/test_resources.py` - 10+ tests for OSDocumentationResources
- `tests/test_stdio_middleware.py` - 15+ tests for STDIO auth and rate limiting
- `tests/test_workflow_planner.py` - 15+ tests for WorkflowPlanner class
- `tests/test_prompts_detailed.py` - 15+ tests for prompts module
- `tests/test_server_functions.py` - 15+ tests for server helper functions
- `tests/test_knowledge_index_builder.py` - 15+ tests for knowledge index
- `tests/test_http_middleware_detailed.py` - 20+ tests for HTTP middleware
- `tests/test_error_envelope_detailed.py` - 20+ tests for error envelopes
- `tests/test_performance.py` - Performance benchmark tests

**Test Files Extended:**
- `tests/test_geography_tools.py` - Added 15+ tests for error paths
- `tests/test_statistics_tools.py` - Added 10+ tests for error handling
- `tests/test_ons_client.py` - Added 10+ tests for edge cases

**Production Deployment:**
- `Dockerfile` - Updated with multi-stage build, non-root user, health check
- `.github/workflows/ci.yml` - Added coverage reporting and Docker build job

### Documentation Added
- **SKILL.md**: Full skills reference covering:
  - Two-step workflow explanation
  - Geographic hierarchy (UK admin levels)
  - Area code formats
  - Common workflow patterns
  - All available tools with descriptions
  - Dataset categories
  - Best practices and error handling

- **docs/mcp_apps_guide.md**: User-facing guide covering:
  - Quick start examples
  - Widget descriptions and features
  - Statistics workflow
  - Feature exploration workflow
  - Cross-widget communication
  - Troubleshooting

- **MCP-Apps Prompt Templates** (13 prompts):
  - Geography: select_uk_areas, find_area_by_postcode, compare_local_authorities
  - Statistics: explore_ons_statistics, census_2021_analysis, area_wellbeing_profile
  - Features: inspect_os_feature, explore_linked_identifiers
  - Routes: plan_walking_route, plan_driving_route, analyze_road_network
  - Cross-widget: area_to_statistics_workflow, feature_to_route_workflow, multi_widget_analysis

---

## Sprint 7: Tool Search Integration ✅ COMPLETE

**Goal**: Implement Anthropic's Tool Search facility to improve context efficiency and tool selection accuracy.

**Background**: With 37+ tools, the project benefits from dynamic tool discovery via `defer_loading: true`, keeping context efficient while maintaining accuracy.

### Tasks

| Task | Status | Notes |
|------|--------|-------|
| 7.1 Tool Search Infrastructure | ✅ Done | Created tool_search_config.py with defer_loading |
| 7.2 MCP Toolset Integration | ✅ Done | Implemented generate_mcp_toolset_config() |
| 7.3 Tool Description Optimization | ✅ Done | Enhanced descriptions with keywords for search |
| 7.4 Testing and Documentation | ✅ Done | 50+ tests, full documentation |

### Files Created
- `src/mcp_service/tool_search_config.py` - Tool categories, defer_loading settings, enhanced descriptions
- `tests/test_tool_search_config.py` - 30+ unit tests for configuration
- `tests/test_tool_search_service.py` - 15+ integration tests for new tool

### New Tool Added
| Tool | Description |
|------|-------------|
| `get_tool_search_config` | Returns tool search configuration, categories, MCP toolset config |

### Tool Categories (Implemented)

| Category | Always Loaded | Deferred |
|----------|---------------|----------|
| Core | hello_world, version_info, route_query | check_api_key, get_tool_search_config |
| Workflow | - | os_ngd_init_mapping_workflow, os_ngd_list_mapping_collections, fetch_detailed_collections, get_single_collection, get_single_collection_queryables |
| Geography | search_geographic_areas, select_geographic_area | fetch_boundaries |
| Statistics | get_statistics | list_ons_datasets, get_dataset_info, compare_areas |
| Features | - | search_features, get_feature, get_bulk_features, inspect_feature, get_feature_with_linked |
| Routes | - | plan_route, get_route_network, get_routing_data |
| Widget | - | get_shared_context, update_shared_context, share_selection |
| Search | - | suggest_collections, suggest_fields, get_knowledge_index_overview |
| Linked | - | get_linked_identifiers, get_bulk_linked_features |
| Utility | - | lookup_addresses, diagnose_address_fields, summarise_buildings_by_road, get_prompt_templates, chat |

### Technical Requirements
- Beta headers: `advanced-tool-use-2025-11-20`, `mcp-client-2025-11-20`
- Supported models: Claude Opus 4.5, Claude Sonnet 4.5
- Two search variants: regex (`tool_search_tool_regex_20251119`) and BM25 (`tool_search_tool_bm25_20251119`)

---

## Sprint 8: Architecture Review & Query Router ✅ COMPLETE

**Goal**: Address the "Birmingham problem" - ensure simple queries use the right tools without complex workflows.

**Background**: Users asking "Find Birmingham" were getting 10+ tool calls through OS NGD workflow when a single `search_geographic_areas` call would suffice.

### Tasks

| Task | Status | Notes |
|------|--------|-------|
| 8.1 Architecture Analysis | ✅ Done | Root cause identified: tool loading priorities |
| 8.2 Query Router Design | ✅ Done | Intent classification with priority rules |
| 8.3 route_query Implementation | ✅ Done | ~500 lines, 8 intent types |
| 8.4 Service Integration | ✅ Done | Added to OSDataHubService, skip_functions |
| 8.5 Tool Config Updates | ✅ Done | route_query, search_geographic_areas, select_geographic_area always-loaded |
| 8.6 Unit Tests | ✅ Done | `tests/test_query_router.py` (~250 lines) |
| 8.7 Documentation | ✅ Done | SKILL.md, CHANGELOG, tutorial updated |
| 8.8 Evaluation Framework | ✅ Done | 30+ questions, 5-dimension rubric, test harness |
| 8.9 Audit Logging | ✅ Done | LLM-readable logs, JSONL output |
| 8.10 Evaluation Score | ✅ Done | 100% on basic+intermediate (21/21) |

### Files Created
- `src/tools/query_router.py` - Query routing and intent classification
- `src/utils/audit_logger.py` - LLM-readable audit logging
- `tests/evaluation/questions.py` - Evaluation question suite
- `tests/evaluation/rubric.py` - Scoring rubric
- `tests/evaluation/harness.py` - Test execution harness
- `tests/test_query_router.py` - Query router unit tests
- `docs/evaluation.md` - Evaluation documentation
- `plans/sprint-8-architecture-review.md` - Architecture analysis document

### New Tool Added
| Tool | Description |
|------|-------------|
| `route_query` | PRIMARY ENTRY POINT - Analyzes query intent, recommends tool and workflow |

### Query Intent Classification

| Intent | Example Query | Recommended Tool |
|--------|--------------|------------------|
| place_lookup | "Find Birmingham" | search_geographic_areas |
| statistics | "Wellbeing in Coventry" | get_statistics |
| area_comparison | "Compare Birmingham and Manchester" | compare_areas |
| feature_search | "Find cinemas near Leeds" | search_features (OS NGD) |
| boundary_fetch | "Get boundary of Coventry" | fetch_boundaries |
| interactive_selection | "Let me select on a map" | select_geographic_area |
| route_planning | "Route from A to B" | plan_route |
| dataset_discovery | "What datasets are available?" | list_ons_datasets |

### Test Results

| Query | Before | After |
|-------|--------|-------|
| "Find Birmingham" | OS NGD workflow (10+ calls) | search_geographic_areas (1 call) |
| "Find cinemas near Leeds" | place_lookup (wrong) | feature_search (correct) |
| "Compare Birmingham and Manchester" | place_lookup (wrong) | area_comparison (correct) |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation | Status |
|------|------------|--------|------------|--------|
| ONS API service name changes | Medium | High | Verified Jan 2025, add monitoring | ✅ Mitigated |
| FastMCP MIME type limitation | Low | Low | Using `text/html` instead of `text/html;profile=mcp-app` | ✅ Resolved |
| Large boundary performance | Medium | Medium | Implement simplification, pagination | 🔲 Pending |
| MCP-Apps spec changes | Low | High | Monitor spec, abstract SDK usage | 🔲 Pending |
| ONS observations API complexity | Medium | Medium | Dimension-handling logic in get_statistics | ✅ Resolved |
| Tool catalog growth | Medium | Medium | Tool search with defer_loading | ✅ Resolved |

---

## Metrics History

| Date | Tests | Tools | Resources | Notes |
|------|-------|-------|-----------|-------|
| 2026-01-18 | 370+ | 38 | 10 | Sprint 8 complete - query router, evaluation framework 100% |
| 2026-01-17 | 370+ | 38 | 10 | Sprint 8 in progress - route_query, architecture review |
| 2026-01-17 | 370+ | 37 | 10 | Sprint 7 complete - tool search, defer_loading |
| 2026-01-17 | 320+ | 36 | 10 | Sprint 6 complete - coverage >80%, Docker, CI/CD |
| 2026-01-17 | 296+ | 36 | 10 | Sprint 6 in progress - coverage 73%, new test files |
| 2026-01-15 | ~210 | 36 | 10 | Sprint 5 complete |
| 2026-01-12 | 141 | 29 | 9 | Sprint 3-4 complete |
| 2025-01-12 | 97 | 25 | 9 | Sprint 1-2 complete |
| (baseline) | 83 | 22 | 6 | Before MCP-Apps work |

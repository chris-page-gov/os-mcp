# MCP-Apps Implementation Progress

This document tracks progress through the [Implementation Roadmap](on-ons%20mcp%20implementation-roadmap.md).

**Last Updated**: 2026-01-15

## Overall Status

| Metric | Value |
|--------|-------|
| Current Sprint | 5 (Complete) |
| Tools Added | 14 (7 geography/statistics + 2 feature inspector + 2 route planner + 3 widget communication) |
| UI Resources Added | 4 (geography-selector, statistics-dashboard, feature-inspector, route-planner) |
| Test Count | ~210 passing (estimated: 141 + 25 feature inspector + 24 route planner + 21 widget communication) |
| Coverage | Pending measurement |

---

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

## Sprint 6: Polish & Release 🔲 NOT STARTED

**Goal**: Production readiness with comprehensive testing and documentation.

### Tasks

| Task | Status | Notes |
|------|--------|-------|
| 6.1 Test coverage >80% | 🔲 Pending | Current: TBD |
| 6.2 Documentation complete | 🔲 Pending | API docs, user guide |
| 6.3 Performance testing | 🔲 Pending | Large boundary handling |
| 6.4 Error handling audit | 🔲 Pending | Edge cases, timeouts |
| 6.5 Production deployment | 🔲 Pending | Docker, CI/CD updates |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation | Status |
|------|------------|--------|------------|--------|
| ONS API service name changes | Medium | High | Verified Jan 2025, add monitoring | ✅ Mitigated |
| FastMCP MIME type limitation | Low | Low | Using `text/html` instead of `text/html;profile=mcp-app` | ✅ Resolved |
| Large boundary performance | Medium | Medium | Implement simplification, pagination | 🔲 Pending |
| MCP-Apps spec changes | Low | High | Monitor spec, abstract SDK usage | 🔲 Pending |
| ONS observations API complexity | Medium | Medium | Dimension-handling logic in get_statistics | ✅ Resolved |

---

## Metrics History

| Date | Tests | Tools | Resources | Notes |
|------|-------|-------|-----------|-------|
| 2026-01-15 | ~210 | 36 | 10 | Sprint 5 complete |
| 2026-01-12 | 141 | 29 | 9 | Sprint 3-4 complete |
| 2025-01-12 | 97 | 25 | 9 | Sprint 1-2 complete |
| (baseline) | 83 | 22 | 6 | Before MCP-Apps work |

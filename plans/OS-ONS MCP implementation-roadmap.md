# OS/ONS MCP-Apps Implementation Roadmap

## Project Overview
Transform the existing os-mcp server into an exemplar MCP-Apps implementation with interactive geographic selection widgets, comprehensive ONS statistics integration, and excellent context building through skills.

## Current State Assessment (Based on Repository)
✅ FastMCP server foundation
✅ OS NGD API integration  
✅ Two-step workflow enforcement
✅ Basic React frontend with Leaflet
✅ HTTP and STDIO transports
✅ Prompt templates with categories
✅ Tool-based feature search

❌ MCP-Apps UI resources (not yet implemented)
❌ ONS API integration (needs expansion)
❌ Interactive boundary selection widgets
❌ Statistical dashboard widgets
❌ Skills documentation for context building

## Priority Lanes

### 🔴 Critical Path (Week 1-2): Core MCP-Apps Foundation
These items are essential for the MCP-Apps functionality and should be completed first.

**1.1 MCP-Apps SDK Integration**
- [ ] Add `@modelcontextprotocol/ext-apps` to dependencies
- [ ] Create `src/ui_resources.py` module for UI resource management
- [ ] Update server initialization to register UI resources
- [ ] Test basic UI resource listing via MCP protocol
- **Deliverable**: Server can list and serve UI resources via `ui://` URIs
- **Time**: 2 days
- **Blocker**: None

**1.2 First UI Widget: Geography Selector**  
- [ ] Create `src/ui/geography_selector.html` with basic structure
- [ ] Implement Leaflet map initialization
- [ ] Add App SDK integration for postMessage communication
- [ ] Create tool `select_geographic_area` with UI resource reference
- [ ] Test widget rendering in Claude Desktop
- **Deliverable**: Working interactive map widget for area selection
- **Time**: 3 days
- **Blocker**: 1.1 must be complete

**1.3 Boundary Fetching Infrastructure**
- [ ] Create `fetch_boundaries_geojson` tool
- [ ] Integrate with ONS Geography API (https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/)
- [ ] Implement boundary simplification based on zoom level
- [ ] Add boundary caching layer
- [ ] Test with different geographic levels (LA, ward, LSOA, etc.)
- **Deliverable**: Reliable boundary data fetching for all UK admin levels
- **Time**: 3 days
- **Blocker**: None (can run parallel to 1.2)

**1.4 Widget Selection Flow**
- [ ] Implement area selection/deselection in widget
- [ ] Handle multi-select mode
- [ ] Send selection results back to host via MCP
- [ ] Update tool response format to include selected areas
- [ ] Add visual feedback for selected areas
- **Deliverable**: Complete end-to-end selection workflow
- **Time**: 2 days  
- **Blocker**: 1.2 and 1.3 must be complete

### 🟡 High Priority (Week 3-4): Statistical Integration

**2.1 ONS API Client**
- [ ] Research and document ONS API endpoints
- [ ] Create `src/ons_client.py` with API wrapper
- [ ] Implement authentication if required
- [ ] Add error handling and rate limiting
- [ ] Create unit tests for ONS client
- **Deliverable**: Reusable ONS API client
- **Time**: 3 days
- **Blocker**: None

**2.2 Statistical Data Tools**
- [ ] Create `query_ons_datasets` tool (list available datasets)
- [ ] Create `get_ons_statistics` tool (fetch data for area)
- [ ] Create `compare_areas_statistics` tool (multi-area comparison)
- [ ] Implement data caching strategy
- [ ] Add response formatting for LLM consumption
- **Deliverable**: Suite of ONS data retrieval tools
- **Time**: 3 days
- **Blocker**: 2.1 must be complete

**2.3 Statistical Dashboard Widget**
- [ ] Create `src/ui/statistics_dashboard.html`
- [ ] Implement Chart.js/D3.js visualizations
- [ ] Add multiple view modes (charts, tables, heatmaps)
- [ ] Implement interactive filtering
- [ ] Add comparison mode for multiple areas
- **Deliverable**: Interactive statistical visualization widget
- **Time**: 4 days
- **Blocker**: 2.2 must be complete

### 🟢 Medium Priority (Week 5-6): Enhanced Features

**3.1 Feature Inspector Widget**
- [ ] Create `src/ui/feature_inspector.html`
- [ ] Display feature properties in formatted table
- [ ] Show linked identifiers with navigation
- [ ] Add spatial relationships visualization
- [ ] Implement export functionality
- **Deliverable**: Detailed feature exploration widget
- **Time**: 3 days
- **Blocker**: Critical path complete

**3.2 Search Enhancement**
- [ ] Add postcode search functionality
- [ ] Implement geographic name search
- [ ] Add autocomplete/suggestions
- [ ] Integrate with widget search boxes
- [ ] Add search history/recent searches
- **Deliverable**: Comprehensive search across all widgets
- **Time**: 2 days
- **Blocker**: 1.2 complete

**3.3 Route Planner Widget** (Optional)
- [ ] Create `src/ui/route_planner.html`
- [ ] Integrate OS Routing API
- [ ] Display turn-by-turn directions
- [ ] Show elevation profiles
- [ ] Add waypoint support
- **Deliverable**: Interactive route planning widget
- **Time**: 4 days
- **Blocker**: Critical path complete

### 🔵 Polish & Documentation (Week 7-8)

**4.1 Skills Documentation**
- [ ] Create `/mnt/skills/user/os-ons-geography/SKILL.md`
- [ ] Document all geographic hierarchy levels
- [ ] Add workflow patterns and best practices
- [ ] Include common use cases with examples
- [ ] Add troubleshooting guide
- **Deliverable**: Comprehensive skills documentation
- **Time**: 2 days
- **Blocker**: All tools and widgets complete for accurate documentation

**4.2 Enhanced Prompt Templates**
- [ ] Update existing prompts to leverage UI widgets
- [ ] Create new prompts for statistical analysis
- [ ] Add multi-step workflows using multiple widgets
- [ ] Include context-building hints in prompts
- **Deliverable**: 10+ production-ready prompt templates
- **Time**: 2 days
- **Blocker**: All widgets complete

**4.3 Testing & Quality Assurance**
- [ ] Write unit tests for all new tools (>80% coverage)
- [ ] Create integration tests for UI widgets
- [ ] Add E2E tests with MCP client
- [ ] Performance testing and optimization
- [ ] Cross-browser testing for widgets
- **Deliverable**: Comprehensive test suite
- **Time**: 4 days
- **Blocker**: Features complete

**4.4 Documentation & Examples**
- [ ] Update README with MCP-Apps examples
- [ ] Create user guide with screenshots
- [ ] Write developer guide for extending widgets
- [ ] Record demo videos
- [ ] Create troubleshooting guide
- **Deliverable**: Complete documentation package
- **Time**: 3 days
- **Blocker**: Testing complete

### ⚪ Future Enhancements (Week 9+)

**5.1 Advanced Analytics**
- [ ] Implement spatial analysis tools
- [ ] Add time-series analysis for statistics
- [ ] Create predictive modeling capabilities
- [ ] Add custom report generation
- **Deliverable**: Advanced analytics features
- **Time**: TBD
- **Blocker**: Core features stable

**5.2 Performance Optimization**
- [ ] Implement advanced caching strategies
- [ ] Add boundary simplification service
- [ ] Optimize widget loading times
- [ ] Add progressive loading for large datasets
- **Deliverable**: <2s widget load times
- **Time**: TBD
- **Blocker**: Performance baseline established

**5.3 Community Features** (Long-term)
- [ ] Enable public sharing of maps
- [ ] Add collaborative selection mode
- [ ] Create area comparison templates
- [ ] Build community dataset library
- **Deliverable**: Social features for collaboration
- **Time**: TBD
- **Blocker**: Core product validated

## Sprint Planning

### Sprint 1 (Days 1-5): MCP-Apps Foundation
**Goal**: Get first widget working end-to-end

Day 1-2:
- Task 1.1: MCP-Apps SDK Integration
- Setup development environment
- Review MCP-Apps specification

Day 3-4:
- Task 1.2: Geography Selector (basic version)
- Task 1.3: Boundary Fetching (start)

Day 5:
- Task 1.3: Boundary Fetching (complete)
- Integration testing
- Sprint retrospective

**Success Criteria**:
- ✅ Geography selector widget renders in Claude Desktop
- ✅ Can select at least one geographic level (e.g., Local Authorities)
- ✅ Widget communicates back to server via MCP

### Sprint 2 (Days 6-10): Selection Flow & Multi-level Support
**Goal**: Complete geography selector with all admin levels

Day 6-7:
- Task 1.4: Widget Selection Flow
- Add multi-select capability

Day 8-9:
- Add remaining geographic levels (wards, LSOAs, MSOAs, OAs)
- Implement level switching in widget
- Add search by postcode

Day 10:
- Polish and bug fixes
- Documentation for geography selector
- Sprint retrospective

**Success Criteria**:
- ✅ Can select multiple areas across all admin levels
- ✅ Selection persists and can be confirmed
- ✅ Postcode search working

### Sprint 3 (Days 11-15): ONS Integration Foundation
**Goal**: Connect to ONS APIs and display basic statistics

Day 11-12:
- Task 2.1: ONS API Client
- Research API endpoints
- Build wrapper library

Day 13-14:
- Task 2.2: Statistical Data Tools
- Implement basic retrieval tools

Day 15:
- Testing and validation
- Sprint retrospective

**Success Criteria**:
- ✅ Can query ONS datasets for a selected area
- ✅ Statistics returned in usable format
- ✅ Error handling works correctly

### Sprint 4 (Days 16-20): Statistical Dashboard
**Goal**: Visual statistical data in interactive widget

Day 16-17:
- Task 2.3: Dashboard Widget (structure)
- Create HTML/CSS layout
- Integrate Chart.js

Day 18-19:
- Task 2.3: Dashboard Widget (data binding)
- Connect to statistical tools
- Implement visualizations

Day 20:
- Polish and testing
- Sprint retrospective

**Success Criteria**:
- ✅ Dashboard renders with real ONS data
- ✅ At least 3 chart types working
- ✅ Filtering and comparison features work

### Sprint 5-6 (Days 21-30): Polish & Scale
**Goal**: Production-ready quality

Week 5:
- Enhanced features (Task 3.1, 3.2)
- Additional widgets as needed
- Performance optimization

Week 6:
- Testing (Task 4.3)
- Documentation (Task 4.1, 4.2, 4.4)
- Deployment preparation

**Success Criteria**:
- ✅ Test coverage >80%
- ✅ Complete documentation
- ✅ Ready for public demo

## Technical Decisions Log

### Decision 1: MCP-Apps SDK vs Custom Implementation
**Decision**: Use official @modelcontextprotocol/ext-apps SDK
**Rationale**: 
- Follows specification exactly
- Benefits from community updates
- Better compatibility with hosts
- Reduces maintenance burden

### Decision 2: Map Library
**Decision**: Stick with Leaflet (already in use)
**Rationale**:
- Lightweight and fast
- Excellent GeoJSON support
- Large plugin ecosystem
- Already integrated in existing frontend

### Decision 3: Chart Library  
**Decision**: Use Chart.js for statistical dashboard
**Rationale**:
- Simpler than D3.js for standard chart types
- Better performance for interactive updates
- Responsive by default
- Easier to maintain

**Alternative Considered**: D3.js
- More powerful but steeper learning curve
- May use for specific advanced visualizations
- Keep as option for Phase 2

### Decision 4: Boundary Data Source
**Decision**: Use ONS Geography API (ArcGIS REST services)
**Rationale**:
- Official, authoritative boundaries
- All UK admin levels available
- Good performance with spatial queries
- Free to use
- GeoJSON output support

### Decision 5: Statistics Data Source
**Decision**: Use ONS APIs (Cantabular, Statistical Bulletins)
**Rationale**:
- Official UK government statistics
- Comprehensive coverage
- Well-documented
- Regular updates
- Programmatic access

### Decision 6: Caching Strategy
**Decision**: In-memory caching with LRU eviction
**Rationale**:
- Boundaries rarely change (1hr TTL acceptable)
- Faster than external cache (Redis)
- Simpler deployment
- Can add Redis later if needed

**Future**: Consider Redis for production if:
- Multiple server instances needed
- Cache size exceeds memory limits
- Need cache persistence across restarts

## Dependencies to Add

```toml
# Add to pyproject.toml

[project.dependencies]
# Existing dependencies...
# Add these:
"aiofiles>=23.0.0",  # For async file operations
"aiocache>=0.12.0",  # For caching utilities
"geojson>=3.0.0",  # GeoJSON utilities
"shapely>=2.0.0",  # Geometry operations

[project.optional-dependencies]
ui = [
    "@modelcontextprotocol/ext-apps>=0.1.0",  # MCP-Apps SDK (npm, but document)
]
```

**Note**: The MCP-Apps SDK is JavaScript/TypeScript, so it's included via CDN in widget HTML files, not in Python dependencies.

## Environment Variables to Add

```bash
# Add to .env / devcontainer.json

# ONS API (if authentication required in future)
ONS_API_KEY=optional_ons_key

# Cache settings
BOUNDARY_CACHE_TTL=3600  # 1 hour in seconds
STATISTICS_CACHE_TTL=1800  # 30 minutes

# Feature flags
ENABLE_ROUTE_PLANNER=false  # Enable when ready
ENABLE_ADVANCED_ANALYTICS=false

# Widget settings
WIDGET_BASE_URL=http://localhost:8000/ui  # For loading widget resources
DEFAULT_MAP_CENTER_LAT=52.4862
DEFAULT_MAP_CENTER_LNG=-1.8904
DEFAULT_MAP_ZOOM=6
```

## Git Branch Strategy

```
main
  ├─ feature/mcp-apps-foundation  (Sprint 1-2)
  ├─ feature/ons-integration       (Sprint 3-4)  
  ├─ feature/enhanced-widgets      (Sprint 5)
  └─ feature/documentation         (Sprint 6)
```

**Workflow**:
1. Create feature branch from main
2. Regular commits with descriptive messages
3. Open PR when sprint complete
4. Code review and testing
5. Merge to main
6. Tag releases: v0.2.0 (MCP-Apps launch), v0.3.0 (ONS integration), etc.

## Success Metrics Tracking

### Technical Metrics
| Metric | Target | Current | Last Updated |
|--------|--------|---------|--------------|
| Widget Load Time (p95) | <2s | TBD | - |
| Tool Response Time (p95) | <1s | TBD | - |
| Test Coverage | >80% | TBD | - |
| Error Rate | <0.1% | TBD | - |

### User Experience Metrics  
| Metric | Target | Current | Last Updated |
|--------|--------|---------|--------------|
| Time to First Selection | <30s | TBD | - |
| Completion Rate | >90% | TBD | - |
| Feature Discovery | >70% | TBD | - |

Update these weekly during development.

## Risk Register

### Risk 1: ONS API Changes
**Probability**: Medium
**Impact**: High
**Mitigation**: 
- Abstract ONS API calls behind client interface
- Version our API client
- Monitor ONS API changelog
- Have fallback to cached/static data

### Risk 2: Browser Compatibility Issues
**Probability**: Medium
**Impact**: Medium
**Mitigation**:
- Test in Chrome, Firefox, Safari
- Use polyfills where needed
- Progressive enhancement approach
- Clear browser requirements in docs

### Risk 3: Performance with Large Boundaries
**Probability**: High
**Impact**: Medium
**Mitigation**:
- Aggressive geometry simplification
- Implement spatial indexing
- Use tiling for very detailed levels
- Progressive loading strategy

### Risk 4: MCP-Apps Spec Changes
**Probability**: Low
**Impact**: High
**Mitigation**:
- Follow official SDK updates closely
- Pin to stable SDK version
- Test against spec compliance regularly
- Participate in MCP community discussions

### Risk 5: Scope Creep
**Probability**: High
**Impact**: Medium
**Mitigation**:
- Stick to roadmap priorities
- Defer enhancements to future phases
- Regular stakeholder check-ins
- Clear MVP definition

## Communication Plan

### Weekly Progress Updates
- Document completed tasks
- Blockers and dependencies
- Updated timeline
- Demo videos/screenshots

### Key Milestones
1. **Week 2**: First widget demo
2. **Week 4**: Full geography selection working
3. **Week 6**: ONS integration complete
4. **Week 8**: Production-ready release

### Demo Schedule
- **Sprint 1 End**: Geography selector basic version
- **Sprint 2 End**: Multi-level selection and search
- **Sprint 3 End**: ONS data retrieval
- **Sprint 4 End**: Statistical dashboard
- **Final**: Complete system with all widgets

## Next Steps (Immediate Actions)

1. **Review this roadmap** - Validate priorities and timeline
2. **Setup development environment** 
   - Clone repo
   - Review existing code structure
   - Test current functionality
3. **Start Sprint 1**
   - Begin Task 1.1: MCP-Apps SDK Integration
   - Read MCP-Apps specification thoroughly
   - Setup UI resources directory structure
4. **Create project board** - Track tasks in GitHub Projects or similar
5. **Schedule regular check-ins** - Weekly progress reviews

## Resources & References

### MCP-Apps Documentation
- [MCP Apps Specification](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/1865)
- [MCP Apps SDK](https://github.com/modelcontextprotocol/ext-apps)
- [MCP Apps Blog Post](http://blog.modelcontextprotocol.io/posts/2025-11-21-mcp-apps/)
- [MCP Apps Tutorial](https://blog.fka.dev/blog/2025-11-22-mcp-apps-101-bringing-interactive-uis-to-ai-conversations/)

### OS Data Hub
- [OS NGD Features API Docs](https://osdatahub.os.uk/docs/ofa/overview)
- [OS Places API](https://osdatahub.os.uk/docs/places/overview)
- [OS Routing API](https://osdatahub.os.uk/docs/routing/overview)

### ONS Resources
- [ONS Geography Portal](https://geoportal.statistics.gov.uk/)
- [ONS Open Geography API](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/)
- [Cantabular API](https://docs.cantabular.com/)
- [NOMIS API](https://www.nomisweb.co.uk/api/v01/help)

### Technical Libraries
- [Leaflet Documentation](https://leafletjs.com/)
- [Chart.js Documentation](https://www.chartjs.org/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

---

**Document Version**: 1.0
**Last Updated**: 2025-01-10
**Author**: Implementation Roadmap for OS/ONS MCP-Apps Server
**Status**: Ready for Review

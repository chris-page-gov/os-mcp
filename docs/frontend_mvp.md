# Public NGD Exploration Frontend MVP

Goal: A browser-based interface that lets any citizen explore Ordnance Survey NGD data via the existing MCP server + a GPT-5 (LLM) model, with guided tutorial prompts and interactive map output.

## Core MVP Objectives
1. Natural language chat (LLM ↔ MCP tools orchestration)
2. Tutorial / guidance pane (click-to-insert prompts)
3. Output pane supporting:
   - Rich text (formatted reasoning & summaries)
   - Tabular data (feature attributes)
   - Map visualisation with data layers (points, polygons, linework)
4. Responsive 3-pane layout (desktop) collapsing to tabbed interface (mobile) similar to Google Notebook LM / notebook UIs.
5. Direct integration with existing MCP HTTP transport (preferred) for tool calls.

## Functional Scope (MVP)
| Feature | Included | Notes |
|---------|----------|-------|
| Chat with GPT-5 | Yes | Streaming tokens, tool call interception |
| Insert tutorial prompt | Yes | Click chip/button adds template to chat input |
| Map display | Yes | Leaflet / MapLibre + simple base layer + vector overlays |
| Layer management | Minimal | Toggle visibility; no styling editor initially |
| Tool result parsing | Yes | Detect GeoJSON vs plain JSON; add to map |
| Routing visualization | Basic | Draw edges/nodes if present; summarise counts |
| Error envelope display | Yes | Non-blocking banner + human-friendly message |
| Session reset | Yes | Clear chat + map layers |
| Mobile tabs | Yes | Tabs: Tutorial | Chat | Output (map/text) |
| Authentication | Simplified | Single public API key (or proxy token) server-side; MCP bearer managed backend |
| Analytics / usage logs | Optional | Simple pageview + tool usage count |
| Download data | Deferred | Future: export GeoJSON / CSV |

## Non-Goals (Initial MVP)
- User accounts / auth flows
- Advanced spatial analysis (buffering, joins)
- Persistent saved projects
- Complex layer styling UI
- Multi-turn plan editing timeline

## Architecture Overview
```
Browser (React) ──► Frontend Backend (Node/Express or Python FastAPI adapter) ──► MCP Server (/mcp HTTP)
                             │                                      │
                             │ (LLM API: GPT-5 via provider) ◄──────┘
                             │
                             └─ Map Tiles (OS base / OpenStreetMap via tile CDN)
```

### Rationale
- Keep MCP server unchanged; expose HTTP `/mcp` + `/health`.
- A lightweight gateway service mediates:
  - Chat turns
  - Tool call translation (JSON envelope construction)
  - Streaming model responses + tool call injection (agent loop)
  - Rate limiting + API key concealment
- Frontend remains static hostable (Netlify / Vercel / S3) if gateway handles secrets.

## Data Flow (Single Turn with Tool Calls)
1. User prompts: "Find cinemas in Leamington"
2. Frontend -> Gateway: POST /chat {message}
3. Gateway streams GPT-5; model decides needs context → emits tool call intent
4. Gateway executes MCP tool sequence: `get_workflow_context` → `fetch_detailed_collections` → `search_features`
5. Aggregated results inserted into model context; final answer streamed back
6. GeoJSON extracted and sent as side-channel event to frontend (WebSocket / SSE) → map layer added

## UI Layout
Desktop (flex 3 columns):
- Left: Tutorial (25%) scrollable; groups: Planning, Routing, Warwickshire, Diagnostics
- Middle: Chat (40%) message list + input footer
- Right: Output (35%) with tabs: [Answer | Map | Data]

Mobile / Narrow (< 900px):
- Top tab bar: Tutorial | Chat | Output
- Only active pane visible; map uses full viewport height minus input area.

## Component Breakdown
| Component | Responsibility |
|-----------|---------------|
| TutorialPanel | Renders grouped clickable prompt chips; search filter |
| ChatWindow | Messages, streaming tokens, tool activity indicators |
| InputBar | Text area + send, attach prompt injection |
| OutputTabs | Switch between text rendering, map, raw data JSON |
| MapView | Leaflet/MapLibre instance, layer registry, fit bounds |
| LayerLegend | Simple toggle list + counts |
| ErrorBanner | Displays retry guidance from error envelope |
| ActivityTimeline (optional) | Collapsible list of tool calls & durations |

## Mapping Considerations
- Library: MapLibre GL (vector) or Leaflet (simpler). MVP choose Leaflet for lighter footprint.
- Base layer: OpenStreetMap tile server (respect usage limits) or OS open tiles if key distribution allowed.
- Layer ingestion: If MCP returns FeatureCollection, add as GeoJSON layer with default style per geometry type.
- Styling heuristics: Points = circle markers, Lines = blue lines, Polygons = semi-transparent fill.
- Fit bounds on first layer add; subsequent layers toggle without resetting unless user clicks "Re-fit".

## Tool Result Handling
| Tool | Map Action |
|------|-----------|
| search_features | Add/merge layer named `search_<collection_id>` |
| get_feature | Highlight feature; optional flash style |
| get_routing_data | Add `routing_nodes` (points) + `routing_edges` (lines) |
| get_bulk_features | Merge features into a single collection layer |
| fetch_detailed_collections | No map; show schema summary in text tab |

## Error Envelope UX
Display: Toast or inline panel with:
- error_code (human mapped e.g., INVALID_COLLECTION → "Unknown collection")
- message
- retry_guidance.hint (if present)
Show "Retry last step" and "Open workflow context" quick actions.

## Security & Rate Limits
- Gateway enforces per-IP rate limiting (e.g., 30 chat turns / hour).
- MCP bearer token not exposed to browser (gateway injects Authorization header).
- LLM provider key only server-side.
- CORS restricted to deployed origin.

## Minimal Gateway Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| /health | GET | Gateway health + MCP pass-through check |
| /chat | POST (stream) | Accepts {message, session_id?} returns streamed events: tokens/tool_events/final |
| /layers | GET | (Optional) Reflect server-known layers for debugging |

## Event Streaming Protocol (Suggestion)
SSE events:
- event: token  data: {"text":"ap..."}
- event: tool   data: {"name":"search_features","status":"start"}
- event: tool   data: {"name":"search_features","status":"end","duration_ms":412}
- event: layer  data: {"layerId":"search_lus-fts-site-1","count":42}
- event: done   data: {}

## Prompt Template Exposure (Public)
Expose a curated safe subset (strip any internal-only keys). Gateway can call `get_prompt_templates` then filter by allowlist regex. Cache for 10 minutes.

## Performance Notes
- Cache `get_workflow_context` per user session to avoid repeated tool latency.
- Debounce tutorial search input.
- Lazy load mapping library only when first map result arrives or user opens Map tab.

## Accessibility
- ARIA roles for tabs, buttons.
- High-contrast map style toggle (dark/light).
- Keyboard: Tab cycle, Enter send, Shift+Enter newline.

## Telemetry (Optional MVP+1)
- Track anonymized: tool call count, average latency, error_code frequency, layers added.
- Exclude user raw prompts unless explicit consent (privacy).

## Testing Strategy
1. Unit: Prompt chip insertion, layer parsing util, error mapper.
2. Integration: Mock gateway -> simulated tool responses for cinema search path.
3. E2E: Cypress/Playwright for: plan query → map layer appears.
4. Load: Concurrent 20 user sessions with cached context.

## Open Questions
- Public OS base tile license for high traffic? Might need proxy + caching.
- Do we need moderation layer on user queries before sending to GPT-5? (Recommended) 
- Session persistence: LocalStorage id vs server-issued session token.

## Recommended Tech Stack
| Layer | Choice |
|-------|--------|
| Frontend | React + Vite + TypeScript |
| UI Library | Minimal (TailwindCSS) to keep bundle small |
| Mapping | Leaflet + leaflet.vectorgrid (later MapLibre) |
| State Mgmt | React Query (server data) + Zustand (UI) |
| Gateway | Node.js (Express) or FastAPI (reuse Python ecosystem) |
| Streaming | Server-Sent Events (simpler than WebSocket initially) |

## MVP Checklist
- [ ] Gateway /chat SSE endpoint calls MCP tools
- [ ] Chat UI with streaming tokens
- [ ] Tutorial panel with clickable template chips
- [ ] Basic three-column responsive layout + mobile tabs
- [ ] Map panel + layer add & toggle
- [ ] Error envelope surfaced & actionable
- [ ] Routing data visualisation (nodes/edges)
- [ ] Health checks aggregate gateway + MCP
- [ ] Basic rate limit & logging

If all above are in place: YES you have a functional MVP enabling exploration.

## Suggested Next (Post-MVP)
- suggest_workflow tool integration (auto-plan) 
- Geo export (download layer as GeoJSON)
- Temporal caching of search results keyed by filter hash
- Workspace save/share link (encoded session state)
- Advanced filtering UI builder referencing enum_queryables.

---
Last Updated: 2025-08-09

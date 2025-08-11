# Frontend Dev Quickstart

Experimental React + Vite + TS UI for the NGD MCP server.

Extended documentation:
- Frontend MVP design: `../docs/frontend_mvp.md`
- Step-by-step tutorial: `../docs/frontend_tutorial.md`

High-level architecture (browser → gateway → MCP) is described in the MVP doc; a concise diagram is included below for quick reference.

```mermaid
flowchart LR
	U[User Browser\nReact App] -->|SSE / REST| G[Gateway (future)] -->|HTTP /mcp JSON| M[MCP Server]
	G -->|LLM API| L[(LLM Provider)]
	M -->|OS Data Hub APIs| D[(OS NGD)]
	U <-->|Tiles| T[(Map Tiles)]
```

## Install

npm install
npm run dev

## Layout

Left: Tutorial / prompt chips
Center: Chat messages
Right: Output panel with tabs (Answer / Map / Data)

## State

Zustand store: messages, layers, activeTab

## Next Steps
- Wire real MCP HTTP calls (SSE or polling) via a gateway module
- Parse tool JSON for FeatureCollections -> add layer metadata
- Render GeoJSON onto Leaflet map
- Provide layer visibility toggles & basic styling
- Error banner + request timing

## Notes
This is an MVP scaffold; no build integration with Python package yet. See the tutorial for full setup and the MVP doc for roadmap/non-goals.

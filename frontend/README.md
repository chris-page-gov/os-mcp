# Frontend Dev Quickstart

Experimental React + Vite + TS UI for the NGD MCP server.

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
This is an MVP scaffold; no build integration with Python package yet.

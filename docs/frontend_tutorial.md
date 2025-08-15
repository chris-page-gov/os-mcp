# Frontend Step-by-Step Tutorial

This guide walks you through running the experimental NGD exploration frontend locally and connecting it to the MCP server.

## Prerequisites
- Python 3.11+
- Node 18+ & npm
- OS API Key (`OS_API_KEY`)
- (Optional) OpenAI API Key (`OPENAI_API_KEY`) to enable the experimental `chat` MCP tool

## 1. Clone & Enter Repo
```bash
git clone https://github.com/chris-page-gov/os-mcp.git
cd os-mcp
```

## 2. Set Environment Variables
Export keys in your shell (or add to devcontainer config and rebuild):
```bash
export OS_API_KEY=YOUR_OS_KEY
# Optional for chat tool
export OPENAI_API_KEY=YOUR_OPENAI_KEY
```

## 3. Start the MCP HTTP Server
Run the server with HTTP transport (separate terminal):
```bash
python -m server --transport streamable-http --host 127.0.0.1 --port 8000
```
Health check (new terminal):
```bash
curl -s http://127.0.0.1:8000/health
```
Expected: `{"status":"ok"}`

## 4. Install Frontend Dependencies
```bash
cd frontend
npm install
```

## 5. Run Frontend Dev Server
```bash
./scripts/dev_frontend.sh --port 5173 --mcp-url http://127.0.0.1:8000/mcp --token dev-token
# (Add --open to auto-open browser)
```
Manual alternative (without readiness checks):
```bash
npm run dev
```
Note the printed local URL (e.g. `http://localhost:5173`). Open it in your browser.

## 6. Interface Overview
- Tutorial (left / tab): clickable prompt chips.
- Chat (middle / tab): messages + input box.
- Output (right / tab): Answer | Map | Data panels.

On narrow screens the layout collapses into tabs.

## 7. First Workflow
Type (or click a tutorial chip that’s similar to):
```
Find the cinema sites in Royal Leamington Spa.
```
If using an agent loop, watch it call `get_workflow_context` → `fetch_detailed_collections` → `search_features`.
When `search_features` returns a FeatureCollection, a layer appears under Map.

If using only the `chat` tool (no automated tool calling yet), you’ll receive reasoning but no data layers; then manually trigger tool calls once wiring is added.

## 8. Viewing Map Data
Open the Map tab:
- The map initializes on first open; subsequent GeoJSON results automatically add layers.
- Toggle layer visibility in the Data tab legend (checkboxes) or remove layers entirely (x button).
- Subsequent searches add additional layers (e.g., `search_lus-fts-site-1`).

## 9. Inspecting Raw Data
Switch to Data tab to view a tabular or raw JSON representation (depending on implementation stage). Use browser devtools for full JSON if truncated.

## 10. Handling Errors
If a tool error occurs you’ll see an error banner with a human-friendly message. Typical recovery:
- `WORKFLOW_CONTEXT_REQUIRED`: run `get_workflow_context` first.
- `INVALID_COLLECTION`: list valid collections or correct the ID.

## 11. Using the Chat Tool
If `OPENAI_API_KEY` is set, you can call the `chat` tool for planning:
```
Plan how to identify cinema sites and then retrieve routing data for a tight bbox around central Leamington.
```
Use its output as guidance before executing actual data tools (either manually or via the agent loop once implemented).

## 12. Resetting Session
Provide a Reset / Clear button (future enhancement) to simultaneously clear chat history, remove map layers, and reset tutorial prompt state.

## 13. Development Tips
- Hot reloading is on by default (Vite).
- Open the browser console to inspect SSE events (`token`, `tool`, `layer`).
- Add temporary logging inside the gateway fetch wrapper for debugging tool envelopes.

## 14. Optional Gateway (Future)
If you build a separate gateway service (recommended for production):
- Frontend sends `/chat` messages to gateway (SSE stream back).
- Gateway handles LLM orchestration and MCP tool envelopes.
- Browser never sees MCP bearer tokens or LLM API keys.

## 15. Testing Frontend Functions
Consider adding simple Jest/Vitest tests for:
- Prompt chip insertion
- GeoJSON layer parsing util
- Error banner mapping from `error_code`

## 16. Troubleshooting
| Symptom | Cause | Fix |
|---------|-------|-----|
| Map empty after search | No GeoJSON returned | Verify tool call & API key |
| Repeated WORKFLOW_CONTEXT_REQUIRED | Skipped context step | Call `get_workflow_context` then retry |
| Chat returns only reasoning | Using `chat` tool alone | Implement / enable agent tool calling |
| 401 on MCP HTTP | Missing/invalid bearer token | Ensure `BEARER_TOKENS` if auth enforced |

## 17. Next Enhancements
- GeoJSON export button
- Layer styling (colour by attribute)
- Offline caching of recent searches
- Shareable session URL (compressed state)

---
Last Updated: 2025-08-11

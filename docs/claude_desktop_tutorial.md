# Claude Desktop Integration Tutorial (Plain Language & Workflows)

This guide shows how to use the `os-mcp` server inside Claude Desktop with natural language. It complements the more technical VS Code and cURL docs.

## 1. What You Get
Once wired into Claude Desktop, you can:
- Ask plain questions (e.g. "Find cinema sites in Leamington Spa") and let Claude decide which MCP tools to call.
- Guide Claude to follow the enforced 2‑step workflow (context → queryables → searches).
- Pull routing slices or linked identifier data for planning workflows.
- Inject curated prompt templates (planning, routing, diagnostics, Warwickshire region) to accelerate reasoning.

## 2. Quick Setup (Stdio via Docker – Recommended for Desktop)
Create / edit your Claude Desktop config (macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`, Linux: `~/.config/Claude/claude_desktop_config.json`). Add an MCP server entry:
```jsonc
{
  "mcpServers": {
    "os-ngd": {
      "command": "docker",
      "args": [
        "run","--rm","-i",
        "-e","OS_API_KEY=YOUR_REAL_KEY",
        "-e","STDIO_KEY=any_value",
        "os-mcp-server"
      ]
    }
  }
}
```
If you prefer running locally without Docker:
```jsonc
{
  "mcpServers": {
    "os-ngd": {
      "command": "python",
      "args": ["-m","server","--transport","stdio"],
      "env": {"OS_API_KEY": "YOUR_REAL_KEY", "STDIO_KEY": "dev"}
    }
  }
}
```
Restart Claude Desktop. The server should appear in the UI (usually shown with available tools/resources).

## 3. First Plain Language Request
In a new Claude chat, just type:
> I want to identify cinema sites in Royal Leamington Spa. Plan the steps first and then execute them.

Ideal tool sequence Claude should decide (summarized):
1. `get_workflow_context` (bootstraps list of collections + rules)
2. `fetch_detailed_collections` (e.g. `lus-fts-site-1`)
3. `search_features` with a filter like `oslandusetertiarygroup = 'Cinema'`

If Claude tries to skip step 1 you’ll see an error envelope with `WORKFLOW_CONTEXT_REQUIRED`; Claude should then recover automatically. You can nudge:
> First call get_workflow_context, then fetch_detailed_collections for the land use site collection before any searches.

JSON envelope example (what Claude sends under the hood):
```json
{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"get_workflow_context","arguments":{}}}
```

## 4. Using Prompt Templates Conversationally
You can explicitly request a template:
> List the available prompt templates.
Claude should call `get_prompt_templates`.

Then:
> Use the search_cinemas_leamington prompt to perform that workflow now.
Claude will extract the instructions from the template text and execute the relevant tools.

Filtering prompts:
> Show only routing prompt templates.
(Triggers `get_prompt_templates` with `{"category":"routing"}`.)

## 5. Example Conversation Transcript (Abbreviated)
User: "Find the primary roads in a small box around Warwick and summarise connectivity."
Claude (internally):
1. Calls `get_workflow_context`
2. Calls `fetch_detailed_collections` (e.g. `trn-ntwk-roadlink-4` if selected)
3. Calls `search_features` with constructed bbox + filter (e.g. classification = 'A Road')
4. Optionally calls `get_routing_data` for network snapshot
Claude (reply): Summarises number of links, sample IDs, maybe suggests follow‑up (turn restrictions, etc.).

## 6. Error & Recovery Patterns (What You Might See)
| Situation | What Happens | What To Say |
|-----------|--------------|-------------|
| Skipped context | Error envelope with `WORKFLOW_CONTEXT_REQUIRED` | "Run get_workflow_context first." |
| Bad collection id | `INVALID_COLLECTION` error_code | "List valid collections then retry with one." |
| Overly complex / malformed filter | `INVALID_INPUT` | Simplify filter or fetch queryables again. |
| Missing enumeration knowledge | Poor filter guess | "Fetch detailed queryables for that collection before filtering." |

## 7. Guided Workflow Prompts (Warwickshire Examples)
Try:
> Use the search_cinemas_leamington prompt.
> Apply routing_network_build_small_bbox for a tiny area near Warwick.
> Run diagnostic_invalid_collection to show the error handling pattern, then fix it.

These instruct the model to follow an embedded plan: you don’t need to craft the tool sequence every time.

## 8. Routing Use Case (Plain Language)
User: "Build a small road network for central Warwick (tight bbox) and list total nodes/edges."
Likely flow:
1. Claude may still obtain workflow context (good practice).
2. Calls `get_routing_data` with your bbox (limit ~100–300).
Reply includes counts; follow with:
> Provide a CSV-style list of the first 10 edges with from/to node IDs and length.
Claude transforms JSON to tabular text (no extra tool call needed).

## 9. Linked Identifiers Scenario
User: "Given this TOID 100000000, show its linked identifiers, then batch check these two TOIDs." Claude may:
1. Call `get_linked_identifiers` (single).
2. Call `get_bulk_linked_features` if you escalate to a batch.
Optionally prompt: "Explain what each featureType means." (Model-only reasoning step.)

## 10. When to Explicitly Direct Tools
Claude usually picks tools, but you can override:
> Call search_features with collection_id trn-ntwk-street-1 filtering usrn = 24501091 limit 1.
If context missing, it will fail then recover. This is useful for rapid testing of a single filter.

## 11. Observing Server Logs
Run locally (without Docker) for richer logs:
```
python -m server --transport stdio --debug
```
Look for request IDs and tool names; errors appear with structured `error_code` fields.

## 12. Automation & Scripting Options
| Approach | Purpose | Notes |
|----------|---------|-------|
| Direct stdio (Claude Desktop) | Natural chat w/ tools | Easiest manual workflow. |
| HTTP + cURL (see `http_usage.md`) | Script / CI | Bypasses chat UI, precise control. |
| Playwright GUI automation | End-to-end UX tests | Heavy; only if you must validate UI flows. |
| Emerging Claude CLI (if/when available) | Script natural prompts + tool routing | Would simplify reproducible transcripts; watch Anthropic announcements. |

At present there’s no official MCP-driving Claude CLI documented; prefer HTTP + scripted tool calls for automated regression tests. For conversation replay, store a sequence of tool envelopes and responses (see `docs/http_usage.md`).

## 13. Tips for Reliable Results
- Always *plan first* explicitly for complex goals (reiterating the 2‑step rule helps model compliance).
- Ask Claude to restate its intended tool sequence before executing ("Outline the plan with the tools you will call") – reduces incorrect early searches.
- For enumerated filters: explicitly instruct "List enum_queryables relevant to classification before building filter." after fetching detailed collections.
- Keep bboxes tight; large bounding boxes can slow responses or exceed upstream timeouts.

## 14. Advanced Prompt Chaining Idea
"Create a multi-stage plan to: (1) find cinemas, (2) find nearest primary road nodes, (3) summarise connectivity density." Claude can:
1. Execute cinema search.
2. Query routing data for overlapping bbox.
3. Provide heuristic proximity reasoning (LLM side). Future enhancement could add a spatial join tool.

## 15. Testing a Fresh Install Quickly
1. Launch Claude Desktop with config.
2. Ask: "List the available OS MCP tools." → Should enumerate tool names.
3. Ask: "Get workflow context for planning." → Should return planning JSON.
4. Ask: "Fetch detailed queryables for lus-fts-site-1." → Tool call.
5. Ask: "Search for cinema land use entries." → Filtered search.
6. Ask: "Show routing prompt templates." → Prompt filter.
7. Ask: "Build a small routing network for this bbox: -1.60,52.27,-1.55,52.30." → get_routing_data.

## 16. Troubleshooting Cheat Sheet
| Symptom | Likely Issue | Quick Fix |
|---------|--------------|-----------|
| No tools appear | Server failed to start | Check Docker logs / STDIO_KEY env. |
| Authentication failed (stdio) | STDIO_KEY unset | Add env var in config. |
| Repeated INVALID_COLLECTION | Typo / out-of-date context | Re-run get_workflow_context. |
| Empty prompt filter | Category mismatch | Use broader substring. |
| Slow first answer | Caching collections | Subsequent calls faster. |

## 17. Roadmap Hooks (You Can Mention to Claude)
You can prime Claude for future capabilities:
> Assume a future suggest_workflow tool exists—explain how you would invoke it for a multi-collection enrichment.
This encourages structured planning even before the tool is implemented.

---
Last Updated: 2025-08-09

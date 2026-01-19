# Client Trace Strategy

This strategy captures enough signal to answer questions like:
- "Is the client using tool search + system prompt, or only the always-loaded tool list?"
- "What tool calls happened in response to a specific conversation?"

It combines a **server-side MCP JSON-RPC trace** with **client-side conversation logs**.

## 1) Capture MCP JSON-RPC Traffic (stdio proxy)

Use the stdio proxy to log every JSON-RPC request/response between the client and the MCP server.
This shows `initialize`, `tools/list`, and `tools/call` traffic, which is the fastest way to confirm
what the client is seeing and how it invokes tools.

### Proxy usage

```
python scripts/mcp_stdio_trace_proxy.py --log logs/mcp-trace.jsonl -- \
  python -m server --transport stdio
```

Then point your MCP client to this proxy command instead of calling `python -m server` directly.

### What to look for in `logs/mcp-trace.jsonl`

- `method: "tools/list"` responses: confirms whether the client is pulling the full tool list.
- `method: "tools/call"` entries: shows actual tool usage and parameters.
- `method: "initialize"`: identifies client capabilities and version metadata.
- Absence of `get_tool_search_config` calls usually means the client is not injecting the tool-search system prompt (confirm via client logs).
- If permission prompts persist, run `diagnose_tool_permissions` to confirm read-only annotations are present.

This does **not** show the user prompt or the model's reasoning; it only shows MCP traffic.

## 2) Capture the Conversation + Thinking Traces (client side)

MCP traffic alone is not enough to confirm how the model reasoned about tool choice.
You need a client-side transcript for that.

Recommended approach:
- Enable the client's debug/trace logging (if supported) and export the full conversation transcript.
- Include the model's "thinking" panel or reasoning trace if the client exposes it.
- Store the transcript alongside the MCP trace log for the same session.

Even when reasoning traces are not available, the **assistant's visible tool-choice explanations**
plus the MCP JSON-RPC log are usually sufficient to reconstruct intent vs. behavior.

## 3) Operational Checklist

- Start a new trace session (fresh log file).
- Run a known prompt (e.g., "Select an OA from Coventry West").
- Save both:
  - `logs/mcp-trace.jsonl` (server-side tool usage)
  - Client transcript / reasoning trace (user + assistant content)
- Review:
  - Did the client call `tools/list`?
  - Did it ever invoke `get_tool_search_config`?
  - Which tool was actually called first?

## 4) Optional: Pair With Audit Logs

If you already use `src/utils/audit_logger.py`, keep those logs in the same folder
and correlate them via timestamps. This gives an additional server-side summary of
routing + tool calls for long sessions.

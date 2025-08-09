# HTTP Usage & cURL Tutorial

This guide shows how to interact with the `os-mcp` server over the streamable HTTP transport using raw `curl` requests.

## 1. Prerequisites
```
export OS_API_KEY=your_real_key
export BEARER_TOKENS=dev-token
```
Python 3.11+, curl, (optional) jq.

## 2. Start Server
```
python -m server --transport streamable-http --host 127.0.0.1 --port 8000
```

## 3. Health & Auth Discovery
```
curl -s http://127.0.0.1:8000/health      # {"status":"ok"}
curl -s http://127.0.0.1:8000/.well-known/mcp-auth | jq
```

## 4. MCP Envelope Format
POST to `/mcp` with JSON like:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": { "name": "get_workflow_context", "arguments": {} }
}
```
Headers:
```
-H "Authorization: Bearer dev-token" -H "Content-Type: application/json"
```
Result payload text is itself JSON (double-parse if needed).

## 5. Helper Function (Bash)
```bash
mcp(){ curl -s -H "Authorization: Bearer dev-token" -H 'Content-Type: application/json' -d "$1" http://127.0.0.1:8000/mcp; }
```

## 6. Workflow Context
```
mcp '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"get_workflow_context","arguments":{}}}' | jq
```

## 7. Fetch Detailed Collections
```
mcp '{"jsonrpc":"2.0","id":"2","method":"tools/call","params":{"name":"fetch_detailed_collections","arguments":{"collection_ids":"lus-fts-site-1"}}}' | jq -r '.result.content[0].text' | jq
```

## 8. Search Features (illustrative filter)
```
mcp '{"jsonrpc":"2.0","id":"3","method":"tools/call","params":{"name":"search_features","arguments":{"collection_id":"lus-fts-site-1","limit":2,"filter":"oslandusetertiarygroup = 'Cinema'"}}}' | jq -r '.result.content[0].text' | jq
```

## 9. Single Feature
```
mcp '{"jsonrpc":"2.0","id":"4","method":"tools/call","params":{"name":"get_feature","arguments":{"collection_id":"lus-fts-site-1","feature_id":"123"}}}' | jq -r '.result.content[0].text' | jq
```

## 10. Linked Identifiers
```
mcp '{"jsonrpc":"2.0","id":"5","method":"tools/call","params":{"name":"get_linked_identifiers","arguments":{"identifier_type":"TOID","identifier":"100000000"}}}' | jq -r '.result.content[0].text' | jq
```

## 11. Bulk Features
```
mcp '{"jsonrpc":"2.0","id":"6","method":"tools/call","params":{"name":"get_bulk_features","arguments":{"collection_id":"lus-fts-site-1","identifiers":["123","456"]}}}' | jq -r '.result.content[0].text' | jq
```

## 12. Prompt Templates (Category Filter)
```
mcp '{"jsonrpc":"2.0","id":"7","method":"tools/call","params":{"name":"get_prompt_templates","arguments":{"category":"routing"}}}' | jq -r '.result.content[0].text' | jq
```

## 13. Routing Data
```
mcp '{"jsonrpc":"2.0","id":"8","method":"tools/call","params":{"name":"get_routing_data","arguments":{"bbox":"-1.60,52.27,-1.55,52.30","limit":100,"include_nodes":true,"include_edges":true}}}' | jq -r '.result.content[0].text' | jq
```

## 14. Errors
- Missing auth → 401 {"detail":"Authentication required"}
- Premature search → WORKFLOW_CONTEXT_REQUIRED envelope
- Invalid collection → INVALID_COLLECTION with suggestions

## 15. End-to-End Script
```
#!/usr/bin/env bash
set -euo pipefail
AUTH='-H Authorization: Bearer dev-token'
endpoint=http://127.0.0.1:8000/mcp
call(){ curl -s $AUTH -H 'Content-Type: application/json' -d "$1" $endpoint | jq -r '.result.content[0].text'; }
call '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"get_workflow_context","arguments":{}}}' >/dev/null
call '{"jsonrpc":"2.0","id":"2","method":"tools/call","params":{"name":"fetch_detailed_collections","arguments":{"collection_ids":"lus-fts-site-1"}}}' >/dev/null
call '{"jsonrpc":"2.0","id":"3","method":"tools/call","params":{"name":"search_features","arguments":{"collection_id":"lus-fts-site-1","limit":2,"filter":"oslandusetertiarygroup = 'Cinema'"}}}' | jq
```

## 16. Health Endpoint & Automation
Use `/health` for readiness probes (CI, dev containers, editor tasks). Example Makefile target:
```
health:
	curl -sf http://127.0.0.1:8000/health | grep '"status"'
```

## 17. Troubleshooting Quick Ref
Issue | Cause | Fix
----- | ----- | ----
401 Unauthorized | Missing bearer | Set BEARER_TOKENS env & header
WORKFLOW_CONTEXT_REQUIRED | Skipped init | Call get_workflow_context first
INVALID_COLLECTION | Wrong id | Re-check list_collections output
Rate limited | Too many rapid calls | Back off (HTTP middleware: 10/min default)

## 18. Next Steps
- Add suggest_workflow tool
- Add /metrics or performance timing tool

---
Last Updated: 2025-08-09

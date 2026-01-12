# OS NGD Workflow Planning Reference

This repo’s MCP server enforces a strict planning workflow to improve result quality.

## Required pattern
1. Call `get_workflow_context`
2. Describe the plan (which collections and why)
3. Call `fetch_detailed_collections` for those collections
4. Only then call `search_features`

## Tips
- Prefer small `limit` values first; paginate with `offset`.
- Keep filters simple; validate field names against queryables.
- If unsure which collections contain an entity type, use `suggest_collections`.

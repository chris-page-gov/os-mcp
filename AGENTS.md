# AGENTS.md

Guidance for AI agents working on this codebase. This document captures common pitfalls and best practices learned from development experience.

## Testing Patterns

### Mocking FastMCP Services

When testing `OSDataHubService` methods, the `register_tools()` method wraps all tool methods with `self.mcp.tool()`. If `mcp` is a plain `MagicMock`, the decorator replaces actual methods with MagicMock objects, causing `TypeError: object MagicMock can't be used in 'await' expression`.

**Problem:**
```python
mock_mcp = MagicMock()
service = OSDataHubService(mock_api, mock_mcp)
# service.get_tool_search_config is now a MagicMock, not the actual async method
await service.get_tool_search_config()  # TypeError!
```

**Solution:** Configure `mcp.tool()` to return a pass-through decorator:
```python
mock_mcp = MagicMock()
mock_mcp.tool.return_value = lambda f: f  # Pass-through decorator
service = OSDataHubService(mock_api, mock_mcp)
# Now service methods remain callable async functions
```

### String Matching in Assertions

When asserting string content, be precise about singular vs plural forms and case sensitivity:

**Problem:**
```python
# Prompt contains "## Available Tool Categories"
assert "Category" in prompt  # Fails - actual text is "Categories"
```

**Solution:** Use lowercase matching with the expected form:
```python
assert "categories" in prompt.lower()  # Matches "Categories", "categories", etc.
```

### Pytest Environment

- Tests require `pytest` and dependencies installed via `pip install -e .[test]`
- Tests should be run from within the devcontainer where dependencies are available
- Use `python -m pytest` if `pytest` command is not found

## Code Patterns

### Adding New Tools

When adding a new tool to `OSDataHubService`:

1. Add the method implementation (async if it performs I/O)
2. Add the tool name to `tool_names` list in `register_tools()`
3. If the tool should bypass workflow context, add to `skip_functions` set
4. Add to `ALWAYS_LOADED_TOOLS` or `DEFERRED_TOOLS` in `tool_search_config.py`
5. Add description entry to `TOOL_DESCRIPTIONS` with:
   - `defer_loading`: boolean matching the tool set membership
   - `category`: appropriate `ToolCategory` enum value
   - `keywords`: list of search terms
   - `description_enhanced`: detailed description for search
6. Write tests with proper mocking (see above)

### Tool Search Configuration

Tools are split into two categories in `src/mcp_service/tool_search_config.py`:

- **ALWAYS_LOADED_TOOLS**: Core entry points, loaded immediately (11 tools)
- **DEFERRED_TOOLS**: Specialized tools discovered via search (26 tools)

The `defer_loading` field in `TOOL_DESCRIPTIONS` must match tool set membership - tests verify this consistency.

## Documentation Requirements

After any code changes, update:

1. **CHANGELOG.md** - Add entry under `[Unreleased]`
2. **plans/PROGRESS.md** - Update task statuses and metrics
3. **README.md** - Update if features/tools changed
4. **CLAUDE.md** - Update if architecture changed

## Git Workflow

- Current development branch: `geo-mcpi`
- Main branch: `main`
- Always verify files are tracked before committing
- Use conventional commit messages

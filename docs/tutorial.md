# OS/ONS MCP Server Tutorial

A hands-on guide to exploring UK geospatial and statistical data using the OS MCP server with Claude Desktop, Claude Code, and Claude Cowork.

## What You'll Learn

This tutorial walks you through:
- Setting up the MCP server with different Claude clients
- Querying UK geographic boundaries and statistics
- Exploring Ordnance Survey mapping data
- Using interactive widgets for visual analysis
- Combining data sources for powerful insights

## Prerequisites

Before starting, you'll need:

1. **OS Data Hub API Key** (free)
   - Register at [OS Data Hub](https://osdatahub.os.uk/)
   - Create a project and copy your API key

2. **Python 3.11+** installed

3. **One or more Claude clients**:
   - [Claude Desktop](https://claude.ai/download) (recommended for widgets)
   - [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (CLI)
   - Claude.ai with Projects/Cowork

---

## Part 1: Installation

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/chris-page-gov/os-mcp.git
cd os-mcp

# Install in editable mode
pip install -e .

# Verify installation
python -m server --help
```

### Quick Smoke Test

```bash
# Set your API key
export OS_API_KEY="your-api-key-here"
export STDIO_KEY="dev-key"

# Test the server starts
./scripts/dev_stdio_list_tools.sh
```

You should see output showing 37 tools available.

---

## Part 2: Client Setup

### Option A: Claude Desktop Setup

Claude Desktop provides the richest experience with interactive widget support.

**Step 1: Build the Docker image** (recommended for isolation)

```bash
cd os-mcp
docker build -t os-mcp-server .
```

**Step 2: Configure Claude Desktop**

Edit your Claude Desktop configuration file:

| Platform | Config Location |
|----------|-----------------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

Add this configuration:

```json
{
  "mcpServers": {
    "os-mcp": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "OS_API_KEY=your-api-key-here",
        "-e", "STDIO_KEY=dev-key",
        "os-mcp-server"
      ]
    }
  }
}
```

**Alternative: Without Docker** (use local Python)

```json
{
  "mcpServers": {
    "os-mcp": {
      "command": "python",
      "args": ["-m", "server", "--transport", "stdio"],
      "env": {
        "OS_API_KEY": "your-api-key-here",
        "STDIO_KEY": "dev-key"
      }
    }
  }
}
```

**Step 3: Restart Claude Desktop**

Close and reopen Claude Desktop. You should see the MCP server icon indicating tools are available.

**Step 4: Verify Connection**

In Claude Desktop, type:
```
What tools do you have available from the os-mcp server?
```

Claude should list the available tools including `search_geographic_areas`, `get_statistics`, etc.

---

### Option B: Claude Code (CLI) Setup

Claude Code connects to MCP servers via the same configuration mechanism.

**Step 1: Create the MCP config directory**

```bash
# macOS/Linux
mkdir -p ~/.config/claude-code

# Create config file
cat > ~/.config/claude-code/config.json << 'EOF'
{
  "mcpServers": {
    "os-mcp": {
      "command": "python",
      "args": ["-m", "server", "--transport", "stdio"],
      "cwd": "/path/to/os-mcp",
      "env": {
        "OS_API_KEY": "your-api-key-here",
        "STDIO_KEY": "dev-key"
      }
    }
  }
}
EOF
```

Replace `/path/to/os-mcp` with the actual path to your cloned repository.

**Step 2: Start Claude Code in the project**

```bash
cd /path/to/os-mcp
claude
```

**Step 3: Verify Connection**

```
> What MCP tools are available?
```

Claude Code should list the os-mcp tools.

**Example CLI Session:**

```
> Search for geographic areas named "Birmingham"

Claude will use the search_geographic_areas tool...
Found: Birmingham (E08000025) - Metropolitan District
```

---

### Option C: Claude Cowork / Projects Setup

For Claude.ai with Projects (Cowork mode), you can use the HTTP transport.

**Step 1: Start the HTTP server**

```bash
export OS_API_KEY="your-api-key-here"
export BEARER_TOKENS="cowork-token"

python -m server --transport streamable-http --host 0.0.0.0 --port 8000
```

**Step 2: Configure as Remote MCP Server**

In your Claude Project settings, add a remote MCP server:

| Setting | Value |
|---------|-------|
| URL | `http://your-server:8000/mcp/` |
| Authentication | Bearer token: `cowork-token` |

**Step 3: Verify Health**

```bash
curl http://localhost:8000/health
# Response: {"status":"ok"}
```

**Note**: For production Cowork deployments, use HTTPS and proper authentication.

---

## Part 3: Tutorial Exercises

### Exercise 1: Your First Query - Find a Local Authority

**Goal**: Search for a UK local authority and get its code.

**In any Claude client, ask:**

```
Find the local authority code for Coventry
```

**What happens:**
1. Claude calls `search_geographic_areas(query="Coventry", level="local_auth")`
2. Returns: `{code: "E08000026", name: "Coventry"}`

**Try it yourself:**
- Search for "Manchester"
- Search for "Edinburgh"
- Search for your home town

---

### Exercise 2: Explore Statistics

**Goal**: Get wellbeing statistics for an area.

**Ask Claude:**

```
What are the wellbeing statistics for Coventry (E08000026)?
```

**What happens:**
1. Claude calls `get_statistics(dataset_id="wellbeing-local-authority", area_codes=["E08000026"])`
2. Returns life satisfaction, happiness, anxiety, and worthwhile scores

**Expected output:**
```
Coventry Wellbeing Statistics:
- Life Satisfaction: 7.4 (out of 10)
- Happiness: 7.3
- Anxiety: 3.1
- Worthwhile: 7.6
```

**Try it yourself:**
- Compare Coventry with Birmingham
- Look up house prices for your area
- Explore census data on qualifications

---

### Exercise 3: Compare Multiple Areas

**Goal**: Compare statistics across several local authorities.

**Ask Claude:**

```
Compare wellbeing between Birmingham, Coventry, and Wolverhampton
```

**What happens:**
1. Claude calls `compare_areas(area_codes=["E08000025", "E08000026", "E08000031"], dataset_id="wellbeing-local-authority")`
2. Returns a comparison table with rankings

**Try it yourself:**
- Compare house prices across the West Midlands
- Compare population in your region
- Rank areas by life expectancy

---

### Exercise 4: Interactive Map Selection (Claude Desktop)

**Goal**: Use the visual geography selector widget.

**Ask Claude Desktop:**

```
Open a map so I can select some local authorities
```

**What happens:**
1. Claude calls `select_geographic_area(level="local_auth", multi_select=true)`
2. An interactive map widget opens
3. You click to select areas
4. Selected codes are returned for further analysis

**Widget Features:**
- Click areas to select/deselect (highlighted in blue)
- Use dropdown to switch geographic levels
- Search by name or postcode
- Multi-select for comparisons

---

### Exercise 5: Explore OS Mapping Data

**Goal**: Search for features using the Ordnance Survey API.

**Ask Claude:**

```
Find cinema sites near Leamington Spa
```

**What happens:**
1. Claude initializes the workflow: `get_workflow_context()`
2. Gets collection details: `fetch_detailed_collections(["lus-fts-site-1"])`
3. Searches: `search_features(collection_id="lus-fts-site-1", filter="oslandusetertiarygroup = 'Cinema'")`

**Important**: OS NGD queries require a 2-step workflow:
1. Initialize with `get_workflow_context()`
2. Fetch queryables with `fetch_detailed_collections()`
3. Then search

**Try it yourself:**
- Find schools in your area
- Search for railway stations
- Look up building footprints

---

### Exercise 6: Inspect a Feature (Claude Desktop)

**Goal**: Use the feature inspector widget.

**Ask Claude:**

```
Inspect the building at this location: 52.4081, -1.5106
```

**What happens:**
1. Claude searches for a building at those coordinates
2. Opens the feature inspector widget showing:
   - All properties in a filterable table
   - Map view with the building geometry
   - Linked identifiers (TOID, UPRN, USRN)
   - Export options (JSON, CSV)

---

### Exercise 7: Plan a Route (Claude Desktop)

**Goal**: Use the route planner widget.

**Ask Claude:**

```
Plan a route from Coventry city centre to Birmingham
```

**What happens:**
1. Claude calls `plan_route(start_lat=52.4081, start_lng=-1.5106, end_lat=52.4862, end_lng=-1.8904)`
2. Opens the route planner widget
3. Shows turn-by-turn directions

**Widget Features:**
- Click map to adjust start/end points
- Add waypoints for multi-stop routes
- View distance and estimated time
- Drag markers to fine-tune positions

---

### Exercise 8: Cross-Widget Workflow

**Goal**: Share data between widgets.

**In Claude Desktop, try this workflow:**

```
1. Open the map and let me select some local authorities
2. Then show me wellbeing statistics for those areas
3. Compare them in a dashboard
```

**What happens:**
1. Geography selector opens, you select areas
2. Claude uses `share_selection()` to pass areas to statistics tools
3. Statistics dashboard shows comparative charts

---

## Part 4: Advanced Topics

### Discovering Available Datasets

```
List all available ONS datasets related to housing
```

Uses: `list_ons_datasets(category="housing")`

### Census 2021 Data

```
Show me qualification levels in Birmingham from the 2021 Census
```

Uses: `list_ons_datasets(category="census", include_census=true)` then `get_statistics(dataset_id="TS067", area_codes=["E08000025"])`

### Linked Identifiers

OS features can be linked across different identifier systems:

| Type | Description |
|------|-------------|
| TOID | Topographic Identifier (buildings, roads) |
| UPRN | Unique Property Reference Number (addresses) |
| USRN | Unique Street Reference Number (streets) |

```
Get the linked UPRNs for building TOID osgb1000000123456
```

### Prompt Templates

The server includes pre-built prompt templates for common workflows:

```
List available prompt templates for statistics workflows
```

Uses: `get_prompt_templates(category="mcp_apps")`

---

## Part 5: Client Comparison

| Feature | Claude Desktop | Claude Code | Cowork |
|---------|---------------|-------------|--------|
| Interactive Widgets | Yes | No (data only) | Partial |
| Map Visualization | Yes | No | Partial |
| Statistics Charts | Yes | No | Partial |
| Tool Calls | Full | Full | Full |
| Local Development | Yes | Yes | Remote |
| Batch Processing | No | Yes | Yes |

**Use Claude Desktop when**: You want visual, interactive exploration

**Use Claude Code when**: You're developing, scripting, or need CLI integration

**Use Cowork when**: Collaborating with others or running remote workflows

---

## Part 6: Troubleshooting

### "WORKFLOW_CONTEXT_REQUIRED" Error

For OS NGD data queries, you must first initialize:

```
Initialize the workflow context, then search for buildings in Coventry
```

### No Statistics Returned

1. Check area code format (e.g., `E08000026` for Coventry)
2. Verify dataset exists: "List available ONS datasets"
3. Some datasets may not have data for all areas

### Widget Not Rendering

1. Ensure you're using Claude Desktop (widgets require MCP-Apps support)
2. Check tool response includes `_meta.uiResourceUris`
3. Try a simpler query first

### Connection Issues

```bash
# Verify server is running
curl http://localhost:8000/health

# Check API key is valid
export OS_API_KEY="your-key"
python -c "import os; print(f'Key set: {len(os.environ.get(\"OS_API_KEY\", \"\")) > 0}')"
```

### Rate Limiting

ONS API limits: 120 requests/10 seconds. If you hit limits:
- Wait a few seconds before retrying
- Reduce batch sizes
- Use caching (automatic for repeated queries)

---

## Quick Reference Card

### Geographic Queries (No workflow init needed)

| Task | Command |
|------|---------|
| Find area by name | `search_geographic_areas(query="Birmingham")` |
| Get boundary GeoJSON | `fetch_boundaries(level="local_auth", codes="E08000025")` |
| Open map selector | `select_geographic_area(level="local_auth")` |

### Statistics Queries (No workflow init needed)

| Task | Command |
|------|---------|
| List datasets | `list_ons_datasets(category="wellbeing")` |
| Get dataset info | `get_dataset_info(dataset_id="wellbeing-local-authority")` |
| Get statistics | `get_statistics(dataset_id="...", area_codes=["E08000026"])` |
| Compare areas | `compare_areas(area_codes=["E08000025","E08000026"], dataset_id="...")` |

### OS NGD Queries (Workflow init required)

| Task | Command |
|------|---------|
| Initialize | `get_workflow_context()` |
| Get queryables | `fetch_detailed_collections(collection_ids=["bld-fts-buildingpart-1"])` |
| Search features | `search_features(collection_id="...", bbox="...", limit=10)` |
| Get single feature | `get_feature(collection_id="...", feature_id="...")` |

### Interactive Widgets (Claude Desktop)

| Widget | Tool |
|--------|------|
| Map selector | `select_geographic_area()` |
| Statistics dashboard | Auto with `get_statistics()` |
| Feature inspector | `inspect_feature()` |
| Route planner | `plan_route()` |

---

## Next Steps

1. **Explore more datasets**: Try `list_ons_datasets()` to discover what's available
2. **Build custom workflows**: Chain tools together for your specific use case
3. **Check the prompt templates**: `get_prompt_templates(category="mcp_apps")` for pre-built patterns
4. **Read the full documentation**: See [SKILL.md](../SKILL.md) and [MCP Apps Guide](mcp_apps_guide.md)

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/chris-page-gov/os-mcp/issues)
- **Documentation**: [Full README](../README.md)
- **API Reference**: [SKILL.md](../SKILL.md)

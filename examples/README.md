# OS MCP Server Examples

This directory contains practical examples demonstrating the functionality of the OS MCP Server using real UK locations.

## Example Locations

- **Nottingham NG1 7FG** - City center location for comprehensive searches
- **Coventry CV1** - City center area for comparison and variety

## Available Examples

### 1. [Basic Usage Examples](./01_basic_usage.py)
- Connection setup and authentication
- Hello world and API key verification
- Getting workflow context

### 2. [Location-Based Searches](./02_location_searches.py)
- Finding specific features around Nottingham and Coventry
- Using bounding boxes for area searches
- Street, building, and land use queries

### 3. [Advanced Filtering Examples](./03_advanced_filtering.py)
- Complex CQL filter expressions
- Enum-based filtering with exact values
- Multi-criteria searches

### 4. [Jupyter Notebook Examples](./examples_notebook.ipynb)
- Interactive demonstrations
- Step-by-step workflows
- Visual outputs and data exploration

### 5. [MCP Client Examples](./05_mcp_client_demo.py)
- Full MCP protocol demonstration
- Real HTTP client connections
- Error handling and edge cases

## Quick Start

1. **Install dependencies:**
   ```bash
   # For Python scripts only
   pip install mcp
   
   # For Jupyter notebook (includes visualization libraries)
   pip install -r examples/requirements.txt
   
   # Or install individual packages
   pip install mcp matplotlib pandas numpy jupyter
   ```

2. **Set up your environment:**
   ```bash
   export OS_API_KEY="your_api_key_here"
   export BEARER_TOKEN="dev-token"
   ```

3. **Run the server:**
   ```bash
   python src/server.py --transport streamable-http
   ```

4. **Try the examples:**
   ```bash
   # Python scripts
   cd examples
   python 01_basic_usage.py
   python 02_location_searches.py
   
   # Jupyter notebook
   jupyter notebook examples_notebook.ipynb
   ```

## Coordinate Systems

All examples use **WGS84 (EPSG:4326)** coordinates:
- **Nottingham NG1 7FG**: Approximately `(-1.1543, 52.9548)`
- **Coventry CV1**: City center around `(-1.5101, 52.4081)`

## Bounding Boxes

For area searches, we use small bounding boxes around our target locations:
- **Nottingham area**: `[-1.16, 52.95, -1.15, 52.96]`
- **Coventry area**: `[-1.52, 52.40, -1.50, 52.42]`

## Data Collections Used

- **`trn-ntwk-street-1`** - Street network data
- **`lus-fts-site-1`** - Land use and site features
- **`bld-fts-buildingline-1`** - Building outlines
- **`adr-fts-addressbasepremium-1`** - Address data

## Common Filters

### Street Searches
```python
# Find A roads
filter="roadclassification = 'A Road'"

# Find streets by name pattern
filter="designatedname1_text LIKE '%high%'"
```

### Land Use Searches
```python
# Find cinemas
filter="oslandusetertiarygroup = 'Cinema'"

# Find retail areas
filter="oslandusetiera = 'Retail'"
```

### Building Searches
```python
# Find specific building themes
filter="theme = 'Buildings'"
```

## Tips for Success

1. **Always start with `get_workflow_context()`** - This is required before any searches
2. **Use exact enum values** - Check the workflow context for available filter values
3. **Plan your approach** - The server enforces planning to explain your search strategy
4. **Use appropriate bounding boxes** - Keep search areas reasonable for performance
5. **Handle rate limits** - The server has built-in rate limiting for API protection

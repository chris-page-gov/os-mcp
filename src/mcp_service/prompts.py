from typing import List, Dict
from mcp.types import PromptMessage, TextContent
from prompt_templates.prompt_templates import PROMPT_TEMPLATES
from utils.logging_config import get_logger

logger = get_logger(__name__)


class OSWorkflowPrompts:
    """Handles registration of OS NGD workflow prompts"""

    def __init__(self, mcp_service):
        self.mcp = mcp_service

    def register_all(self) -> None:
        """Register all workflow prompts"""
        self._register_getting_started_prompt()
        self._register_analysis_prompts()
        self._register_general_prompts()

    def _register_getting_started_prompt(self) -> None:
        """Register the critical getting started prompt.

        IMPORTANT: This prompt should be read first by any client.
        It explains to ALWAYS call route_query before other tools.
        """

        @self.mcp.prompt()
        def getting_started() -> List[PromptMessage]:
            """CRITICAL: Read this first before using any tools.

            This prompt explains the correct way to use this MCP server:
            1. ALWAYS call route_query FIRST for any user query
            2. route_query will recommend the correct tool and workflow
            3. This prevents common mistakes like using OS NGD for simple place lookups
            """
            return [
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text="""# CRITICAL: How to Use This MCP Server

## ALWAYS Call route_query FIRST

For ANY user query, call `route_query` first to get the correct tool recommendation:

```
route_query("Find Birmingham")
→ Recommends: search_geographic_areas (NOT OS NGD workflow)

route_query("Find cinemas in Leeds")
→ Recommends: OS NGD workflow (search_features)
```

## Why This Matters

This server has 39 tools serving DIFFERENT purposes:
- **ONS Geography API** (search_geographic_areas) - For finding places by NAME
- **ONS Statistics API** (get_statistics, compare_areas) - For government statistics
- **OS NGD Mapping API** (os_ngd_init_mapping_workflow, search_features) - For MAPPING features (buildings, roads) - ⛔ SPECIALIZED

WITHOUT route_query, it's easy to make mistakes like:
- Using OS NGD's gnm-fts-namedarea for "find Birmingham" (WRONG - use search_geographic_areas)
- Using search_geographic_areas for "find cinemas" (WRONG - use OS NGD workflow)

## Quick Decision Table

| User Query | route_query Intent | Correct Tool |
|------------|-------------------|--------------|
| "Find Birmingham" | place_lookup | search_geographic_areas |
| "Local authority code for Coventry" | place_lookup | search_geographic_areas |
| "Find cinemas in Leeds" | feature_search | OS NGD workflow |
| "Population of Manchester" | statistics | get_statistics |
| "Compare Birmingham and London" | area_comparison | compare_areas |

## REMEMBER: route_query FIRST, then follow its recommendation.""",
                    ),
                )
            ]

    def _register_analysis_prompts(self) -> None:
        """Register analysis workflow prompts"""

        @self.mcp.prompt()
        def usrn_breakdown_analysis(usrn: str) -> List[PromptMessage]:
            """Generate a step-by-step USRN breakdown workflow"""
            template = PROMPT_TEMPLATES["usrn_breakdown"].format(usrn=usrn)

            return [
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"As an expert in OS NGD API workflows and transport network analysis, {template}",
                    ),
                )
            ]

    def _register_general_prompts(self) -> None:
        """Register general OS NGD guidance prompts"""

        @self.mcp.prompt()
        def collection_query_guidance(
            collection_id: str, query_type: str = "features"
        ) -> List[PromptMessage]:
            """Generate guidance for querying OS NGD collections"""
            return [
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"As an OS NGD API expert, guide me through querying the '{collection_id}' collection for {query_type}. "
                        f"Include: 1) Available filters, 2) Best practices for bbox queries, "
                        f"3) CRS considerations, 4) Example queries with proper syntax.",
                    ),
                )
            ]

        @self.mcp.prompt()
        def workflow_planning(
            user_request: str, data_theme: str = "transport"
        ) -> List[PromptMessage]:
            """Generate a workflow plan for complex OS NGD queries"""
            return [
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"As a geospatial workflow planner, create a detailed workflow plan for: '{user_request}'. "
                        f"Focus on {data_theme} theme data. Include: "
                        f"1) Collection selection rationale, "
                        f"2) Query sequence with dependencies, "
                        f"3) Filter strategies, "
                        f"4) Error handling considerations.",
                    ),
                )
            ]


def get_prompt_templates(category: str | None = None) -> Dict[str, str]:
    """Return prompt templates with optional substring category filtering.

    Special case: category 'warwickshire' returns ALL Warwickshire prompts even
    if individual keys don't contain the substring.
    """
    from prompt_templates.prompt_templates import PROMPT_TEMPLATES  # local import to ensure merge executed

    if category:
        needle = category.lower()
        if needle == "warwickshire":
            try:  # pragma: no cover
                from prompt_templates.warwickshire import WARWICKSHIRE_PROMPTS  # type: ignore

                return {k: v for k, v in PROMPT_TEMPLATES.items() if k in WARWICKSHIRE_PROMPTS}
            except Exception:
                pass
        return {k: v for k, v in PROMPT_TEMPLATES.items() if needle in k.lower()}
    return PROMPT_TEMPLATES

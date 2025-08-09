"""Category-specific prompt filtering tests."""
from typing import Set

from mcp_service.prompts import get_prompt_templates
from prompt_templates.prompt_templates import PROMPT_TEMPLATES
from prompt_templates.warwickshire import WARWICKSHIRE_PROMPTS
from prompt_templates.planning import PLANNING_PROMPTS
from prompt_templates.routing import ROUTING_PROMPTS
from prompt_templates.diagnostics import DIAGNOSTICS_PROMPTS


def test_category_warwickshire_exact_set() -> None:
    subset = get_prompt_templates("warwickshire")
    assert set(subset.keys()) == set(WARWICKSHIRE_PROMPTS.keys())
    # Ensure a base prompt not in module isn't included
    assert "usrn_breakdown" not in subset


def test_category_planning_includes_generic_and_regional() -> None:
    subset = get_prompt_templates("planning")
    for key in PLANNING_PROMPTS:
        assert key in subset
    regional_planning_keys = {k for k in WARWICKSHIRE_PROMPTS if k.startswith("planning_")}
    assert regional_planning_keys, "Expected at least one regional planning key"
    for key in regional_planning_keys:
        assert key in subset
    expected: Set[str] = {k for k in PROMPT_TEMPLATES if "planning" in k}
    assert set(subset.keys()) == expected


def test_category_routing_only_routing_keys() -> None:
    subset = get_prompt_templates("routing")
    for key in ROUTING_PROMPTS:
        assert key in subset
    assert "route_network_build_small_bbox" not in subset  # does not contain substring
    expected = {k for k in PROMPT_TEMPLATES if "routing" in k}
    assert set(subset.keys()) == expected


def test_category_diagnostics_excludes_singular_warwickshire_keys() -> None:
    subset = get_prompt_templates("diagnostics")
    for key in DIAGNOSTICS_PROMPTS:
        assert key in subset
    warwick_diag = {k for k in WARWICKSHIRE_PROMPTS if k.startswith("diagnostic_")}
    assert warwick_diag, "Expected warwickshire diagnostic keys present in module"
    assert not (warwick_diag & set(subset.keys()))


def test_category_diagnostic_includes_warwickshire_singular() -> None:
    subset = get_prompt_templates("diagnostic")
    warwick_diag = {k for k in WARWICKSHIRE_PROMPTS if k.startswith("diagnostic_")}
    assert warwick_diag & set(subset.keys()), "Expected warwickshire diagnostic prompts in 'diagnostic' filter"


def test_unknown_category_returns_empty() -> None:
    subset = get_prompt_templates("nonexistent_category")
    assert subset == {}

from mcp_service.prompts import get_prompt_templates


def test_warwickshire_prompt_subset() -> None:
    prompts = get_prompt_templates(category="warwickshire")
    assert prompts, "Expected warwickshire prompts to be present"
    assert "search_cinemas_leamington" in prompts
    assert any(k.startswith("diagnostic_") for k in prompts)


def test_warwickshire_prompt_unfiltered_contains_all() -> None:
    subset = get_prompt_templates(category="warwickshire")
    all_prompts = get_prompt_templates()
    for k in subset:
        assert k in all_prompts

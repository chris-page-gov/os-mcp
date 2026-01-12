"""ONS Statistics Tools with MCP-Apps UI support

This module provides tools for discovering and retrieving UK statistics
from the Office for National Statistics (ONS) API.

Tools in this module:
- list_ons_datasets: Lists available ONS datasets
- get_dataset_info: Gets metadata for a specific dataset
- get_statistics: Retrieves statistical observations for geographic areas
- compare_areas: Compares statistics across multiple areas
"""

import json
import logging
from typing import Any, Dict, List, Optional

from clients.ons_client import ONSAPIClient, ONSAPIError
from utils.error_envelope import build_error_envelope, ErrorCode

logger = logging.getLogger(__name__)

# Common dataset categories for easier discovery
DATASET_CATEGORIES = {
    "wellbeing": ["wellbeing-local-authority", "wellbeing-quarterly"],
    "economy": ["gdp-by-local-authority", "regional-gdp-by-year", "regional-gdp-by-quarter"],
    "housing": ["house-prices-local-authority"],
    "population": ["mid-year-pop-est", "ageing-population-estimates"],
    "health": ["life-expectancy-by-local-authority", "weekly-deaths-local-authority"],
    "employment": ["ashe-tables-7-and-8", "uk-business-by-enterprises-and-local-units"],
    "census": [],  # Populated dynamically via is_based_on=UR
}


# ============================================================================
# Tool implementations (to be registered in OSDataHubService)
# ============================================================================


async def list_ons_datasets(
    category: Optional[str] = None,
    search: Optional[str] = None,
    include_census: bool = False,
    limit: int = 50,
) -> str:
    """List available ONS datasets.

    Discover datasets available from the Office for National Statistics API.
    Use the returned dataset IDs with get_statistics to fetch actual data.

    Args:
        category: Filter by category. Options:
                  - wellbeing: Life satisfaction, happiness, anxiety
                  - economy: GDP, regional economic data
                  - housing: House prices
                  - population: Population estimates, demographics
                  - health: Life expectancy, mortality
                  - employment: Earnings, businesses
                  - census: Census 2021 datasets (requires include_census=True)
        search: Search term to filter datasets by title/description
        include_census: Include Census 2021 datasets (default: False, as there are 30+)
        limit: Maximum datasets to return (default: 50, max: 100)

    Returns:
        JSON with list of datasets including id, title, description

    Examples:
        # List all local authority datasets
        list_ons_datasets()

        # Search for housing-related data
        list_ons_datasets(search="house price")

        # Get Census 2021 datasets
        list_ons_datasets(category="census", include_census=True)
    """
    limit = min(max(1, limit), 100)

    try:
        async with ONSAPIClient() as client:
            datasets: List[Dict[str, Any]] = []

            # Handle category filtering
            if category:
                category_lower = category.lower()
                if category_lower == "census":
                    if include_census:
                        datasets = await client.list_census_datasets()
                    else:
                        return json.dumps({
                            "status": "info",
                            "message": "Set include_census=True to list Census 2021 datasets (30+ datasets)",
                            "hint": "Census datasets have codes like TS063 (Occupation), TS067 (Qualifications)",
                        })
                elif category_lower in DATASET_CATEGORIES:
                    # Get specific datasets for category
                    for dataset_id in DATASET_CATEGORIES[category_lower]:
                        try:
                            ds = await client.get_dataset(dataset_id)
                            datasets.append(ds)
                        except ONSAPIError:
                            continue
                else:
                    return json.dumps(
                        build_error_envelope(
                            tool="list_ons_datasets",
                            code=ErrorCode.INVALID_INPUT,
                            message=f"Unknown category '{category}'",
                            details={"available_categories": list(DATASET_CATEGORIES.keys())},
                        )
                    )

            # Handle search
            elif search:
                datasets = await client.search_datasets(search)

            # Default: list local authority datasets
            else:
                datasets = await client.list_local_authority_datasets()

            # Apply limit
            datasets = datasets[:limit]

            # Format response
            results = []
            for ds in datasets:
                results.append({
                    "id": ds.get("id"),
                    "title": ds.get("title"),
                    "description": ds.get("description", "")[:200],
                    "keywords": ds.get("keywords", []),
                    "last_updated": ds.get("last_updated"),
                    "release_frequency": ds.get("release_frequency"),
                })

            return json.dumps({
                "count": len(results),
                "datasets": results,
                "category": category,
                "search": search,
            })

    except ONSAPIError as e:
        logger.error(f"ONS API error: {e}")
        return json.dumps(
            build_error_envelope(
                tool="list_ons_datasets",
                code=ErrorCode.UPSTREAM_ERROR,
                message=str(e),
            )
        )
    except Exception as e:
        logger.error(f"Error listing datasets: {e}")
        return json.dumps(
            build_error_envelope(
                tool="list_ons_datasets",
                code=ErrorCode.GENERAL_ERROR,
                message=str(e),
            )
        )


async def get_dataset_info(dataset_id: str) -> str:
    """Get detailed information about a specific ONS dataset.

    Retrieves metadata including available dimensions, editions, and versions.
    Use this to understand what data is available before calling get_statistics.

    Args:
        dataset_id: The dataset identifier (e.g., "wellbeing-local-authority")
                   Get IDs from list_ons_datasets

    Returns:
        JSON with dataset metadata, dimensions, and data structure

    Examples:
        # Get info about wellbeing dataset
        get_dataset_info(dataset_id="wellbeing-local-authority")

        # Get info about house prices
        get_dataset_info(dataset_id="house-prices-local-authority")
    """
    if not dataset_id or not dataset_id.strip():
        return json.dumps(
            build_error_envelope(
                tool="get_dataset_info",
                code=ErrorCode.INVALID_INPUT,
                message="dataset_id is required",
            )
        )

    try:
        async with ONSAPIClient() as client:
            # Get dataset metadata
            dataset = await client.get_dataset(dataset_id)

            # Get editions
            editions_data = await client.list_editions(dataset_id)
            editions = editions_data.get("items", [])

            # Get latest version dimensions if available
            dimensions = []
            if editions:
                first_edition = editions[0].get("edition", "time-series")
                try:
                    latest = await client.get_latest_version(dataset_id, first_edition)
                    dimensions = latest.get("dimensions", [])
                except ONSAPIError:
                    pass

            return json.dumps({
                "id": dataset.get("id"),
                "title": dataset.get("title"),
                "description": dataset.get("description"),
                "contacts": dataset.get("contacts", []),
                "keywords": dataset.get("keywords", []),
                "release_frequency": dataset.get("release_frequency"),
                "last_updated": dataset.get("last_updated"),
                "national_statistic": dataset.get("national_statistic", False),
                "editions": [e.get("edition") for e in editions],
                "dimensions": [
                    {"name": d.get("name"), "label": d.get("label", d.get("name"))}
                    for d in dimensions
                ],
                "links": {
                    "self": dataset.get("links", {}).get("self", {}).get("href"),
                },
            })

    except ONSAPIError as e:
        logger.error(f"ONS API error: {e}")
        if e.status_code == 404:
            return json.dumps(
                build_error_envelope(
                    tool="get_dataset_info",
                    code=ErrorCode.INVALID_INPUT,
                    message=f"Dataset '{dataset_id}' not found",
                    details={"hint": "Use list_ons_datasets to find valid dataset IDs"},
                )
            )
        return json.dumps(
            build_error_envelope(
                tool="get_dataset_info",
                code=ErrorCode.UPSTREAM_ERROR,
                message=str(e),
            )
        )
    except Exception as e:
        logger.error(f"Error getting dataset info: {e}")
        return json.dumps(
            build_error_envelope(
                tool="get_dataset_info",
                code=ErrorCode.GENERAL_ERROR,
                message=str(e),
            )
        )


async def get_statistics(
    dataset_id: str,
    area_code: Optional[str] = None,
    time_period: Optional[str] = None,
    measure: Optional[str] = None,
) -> str:
    """Get statistical observations from an ONS dataset.

    Retrieves data for a specific geographic area. The ONS API requires specific
    dimension values - use get_dataset_info first to see available dimensions.

    For wellbeing-local-authority, common measures are:
    - life-satisfaction, worthwhile, happiness, anxiety
    With estimates: average-mean, median, poor, good, very-good

    Args:
        dataset_id: The dataset identifier (e.g., "wellbeing-local-authority")
        area_code: GSS code (e.g., "E08000026" for Coventry, "K02000001" for UK)
        time_period: Time period (e.g., "2022-23"). Use "*" for all periods.
        measure: Measure/indicator name (dataset-specific)

    Returns:
        JSON with observation data, linked to statistics dashboard

    Examples:
        # Get life satisfaction for Coventry over time
        get_statistics(
            dataset_id="wellbeing-local-authority",
            area_code="E08000026",
            time_period="*",
            measure="life-satisfaction"
        )
    """
    if not dataset_id or not dataset_id.strip():
        return json.dumps(
            build_error_envelope(
                tool="get_statistics",
                code=ErrorCode.INVALID_INPUT,
                message="dataset_id is required",
            )
        )

    try:
        async with ONSAPIClient() as client:
            # Get dataset info to understand dimensions
            ds_info = await client.get_dataset(dataset_id)
            dataset_title = ds_info.get("title", dataset_id)

            # Get dimensions for this dataset
            try:
                version_info = await client.get_latest_version(dataset_id)
                dims = version_info.get("dimensions", [])
                dim_names = [d.get("name") for d in dims]
            except ONSAPIError:
                dims = []
                dim_names = []

            # Build dimension parameters based on dataset
            dimensions: Dict[str, str] = {}
            wildcard_dim: Optional[str] = None

            # Common dimension mappings
            if area_code:
                if "geography" in dim_names:
                    dimensions["geography"] = area_code

            if time_period:
                if time_period == "*":
                    wildcard_dim = "time"
                elif "time" in dim_names:
                    dimensions["time"] = time_period

            # Handle wellbeing-specific dimensions
            if dataset_id == "wellbeing-local-authority":
                dimensions["estimate"] = "average-mean"
                if measure:
                    dimensions["measureofwellbeing"] = measure
                else:
                    dimensions["measureofwellbeing"] = "life-satisfaction"
                if not wildcard_dim and "time" not in dimensions:
                    wildcard_dim = "time"

            # Attempt to get observations
            try:
                result = await client.get_observations(
                    dataset_id,
                    dimensions=dimensions if dimensions else None,
                    wildcard_dimension=wildcard_dim,
                )

                # Parse observation from response
                observation = result.get("observation")
                observations_list = result.get("observations", [])

                # Handle single observation vs list
                if observation is not None and not observations_list:
                    observations_list = [{
                        "value": observation,
                        "dimensions": result.get("dimensions", {}),
                    }]

                return json.dumps({
                    "status": "ok",
                    "dataset_id": dataset_id,
                    "dataset_title": dataset_title,
                    "area_code": area_code,
                    "observation_count": len(observations_list) if observations_list else 1,
                    "observation": observation,
                    "observations": observations_list,
                    "dimensions_used": dimensions,
                    "available_dimensions": dim_names,
                    "_meta": {
                        "uiResourceUris": ["ui://os-ons/statistics-dashboard"],
                        "audience": ["user"],
                    },
                })

            except ONSAPIError as e:
                # Return helpful error with dimension info
                return json.dumps({
                    "status": "error",
                    "error": str(e),
                    "dataset_id": dataset_id,
                    "available_dimensions": dim_names,
                    "hint": "Use get_dataset_info to see available dimension values",
                    "dimensions_attempted": dimensions,
                })

    except ONSAPIError as e:
        logger.error(f"ONS API error: {e}")
        return json.dumps(
            build_error_envelope(
                tool="get_statistics",
                code=ErrorCode.UPSTREAM_ERROR,
                message=str(e),
            )
        )
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return json.dumps(
            build_error_envelope(
                tool="get_statistics",
                code=ErrorCode.GENERAL_ERROR,
                message=str(e),
            )
        )


async def compare_areas(
    dataset_id: str,
    area_codes: str,
    time_period: Optional[str] = None,
) -> str:
    """Compare statistics across multiple geographic areas.

    Fetches data for multiple areas and formats it for side-by-side comparison
    in the statistics dashboard.

    Args:
        dataset_id: The dataset identifier (e.g., "wellbeing-local-authority")
        area_codes: Comma-separated GSS codes (e.g., "E08000026,E08000025,E08000027")
                   Minimum 2 areas, maximum 10
        time_period: Optional time filter for comparison

    Returns:
        JSON with comparison data structured for visualization

    Examples:
        # Compare wellbeing across West Midlands cities
        compare_areas(
            dataset_id="wellbeing-local-authority",
            area_codes="E08000025,E08000026,E08000027"
        )
    """
    if not dataset_id or not dataset_id.strip():
        return json.dumps(
            build_error_envelope(
                tool="compare_areas",
                code=ErrorCode.INVALID_INPUT,
                message="dataset_id is required",
            )
        )

    if not area_codes or not area_codes.strip():
        return json.dumps(
            build_error_envelope(
                tool="compare_areas",
                code=ErrorCode.INVALID_INPUT,
                message="area_codes is required (comma-separated GSS codes)",
            )
        )

    codes = [c.strip() for c in area_codes.split(",") if c.strip()]

    if len(codes) < 2:
        return json.dumps(
            build_error_envelope(
                tool="compare_areas",
                code=ErrorCode.INVALID_INPUT,
                message="At least 2 area codes required for comparison",
            )
        )

    if len(codes) > 10:
        codes = codes[:10]  # Limit to 10 areas

    try:
        async with ONSAPIClient() as client:
            # Get dataset info
            ds_info = await client.get_dataset(dataset_id)
            dataset_title = ds_info.get("title", dataset_id)

            # Fetch data for each area
            comparison_data: List[Dict[str, Any]] = []

            for code in codes:
                try:
                    dimensions: Dict[str, str] = {"geography": code}
                    if time_period:
                        dimensions["time"] = time_period

                    result = await client.get_observations(
                        dataset_id,
                        dimensions=dimensions,
                        limit=50,
                    )

                    observations = result.get("observations", [])

                    comparison_data.append({
                        "area_code": code,
                        "observations": observations,
                        "observation_count": len(observations),
                    })

                except ONSAPIError as e:
                    logger.warning(f"Error fetching data for {code}: {e}")
                    comparison_data.append({
                        "area_code": code,
                        "error": str(e),
                        "observations": [],
                    })

            return json.dumps({
                "status": "ok",
                "dataset_id": dataset_id,
                "dataset_title": dataset_title,
                "time_period": time_period,
                "area_count": len(codes),
                "comparison": comparison_data,
                "_meta": {
                    "uiResourceUris": ["ui://os-ons/statistics-dashboard"],
                    "audience": ["user"],
                },
            })

    except ONSAPIError as e:
        logger.error(f"ONS API error: {e}")
        return json.dumps(
            build_error_envelope(
                tool="compare_areas",
                code=ErrorCode.UPSTREAM_ERROR,
                message=str(e),
            )
        )
    except Exception as e:
        logger.error(f"Error comparing areas: {e}")
        return json.dumps(
            build_error_envelope(
                tool="compare_areas",
                code=ErrorCode.GENERAL_ERROR,
                message=str(e),
            )
        )

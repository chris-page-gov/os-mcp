"""ONS Statistics API Client

Client for accessing Office for National Statistics (ONS) data via their
public Beta API (https://api.beta.ons.gov.uk/v1).

API Documentation: https://developer.ons.gov.uk/

Key Features:
- No authentication required (open API)
- Rate limits: 120 req/10s, 200 req/min
- Supports Census 2021 datasets and local authority statistics
"""

import asyncio
import logging
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

logger = logging.getLogger(__name__)

# ONS Beta API base URL
ONS_API_BASE = "https://api.beta.ons.gov.uk/v1"

# Rate limiting: 120 requests per 10 seconds
RATE_LIMIT_REQUESTS = 120
RATE_LIMIT_WINDOW = 10  # seconds

# Cache TTL in seconds (1 hour for dataset metadata)
CACHE_TTL = 3600


class ONSRateLimiter:
    """Simple rate limiter for ONS API (120 req/10s)"""

    def __init__(self, max_requests: int = RATE_LIMIT_REQUESTS, window: int = RATE_LIMIT_WINDOW):
        self.max_requests = max_requests
        self.window = window
        self.requests: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait if necessary to respect rate limits"""
        async with self._lock:
            now = time.time()
            # Remove old requests outside the window
            self.requests = [t for t in self.requests if now - t < self.window]

            if len(self.requests) >= self.max_requests:
                # Wait until oldest request expires
                sleep_time = self.window - (now - self.requests[0])
                if sleep_time > 0:
                    logger.debug(f"Rate limit reached, sleeping {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
                    self.requests = []

            self.requests.append(time.time())


class ONSCache:
    """Simple in-memory cache with TTL"""

    def __init__(self, ttl: int = CACHE_TTL):
        self.ttl = ttl
        self._cache: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self._cache:
            timestamp, value = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        self._cache[key] = (time.time(), value)

    def clear(self) -> None:
        """Clear all cached values"""
        self._cache.clear()


class ONSAPIClient:
    """Client for ONS Statistics API

    Usage:
        async with ONSAPIClient() as client:
            datasets = await client.list_datasets()
            data = await client.get_observations("wellbeing-local-authority", area="E08000026")
    """

    def __init__(self, timeout: int = 30, enable_cache: bool = True):
        self.base_url = ONS_API_BASE
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.rate_limiter = ONSRateLimiter()
        self.cache = ONSCache() if enable_cache else None
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "ONSAPIClient":
        self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get existing aiohttp session or raise if not initialized."""
        if self._session is None:
            raise RuntimeError("ONSAPIClient session not initialized; use 'async with ONSAPIClient()'.")
        return self._session

    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Make a GET request to ONS API with rate limiting and caching"""
        url = f"{self.base_url}{endpoint}"
        cache_key = f"{endpoint}:{params}" if params else endpoint

        # Check cache
        if use_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit: {endpoint}")
                return cached

        # Rate limit
        await self.rate_limiter.acquire()

        # Make request
        session = await self._get_session()
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 429:
                    # Rate limited - wait and retry
                    retry_after = int(resp.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    return await self._request(endpoint, params, use_cache)

                if resp.status != 200:
                    text = await resp.text()
                    raise ONSAPIError(f"ONS API error {resp.status}: {text[:200]}", resp.status)

                data = await resp.json()

                # Cache result
                if use_cache and self.cache:
                    self.cache.set(cache_key, data)

                return data
        except aiohttp.ClientError as exc:
            raise ONSAPIError(f"ONS API connection error: {exc}") from exc

    # =========================================================================
    # Dataset Discovery
    # =========================================================================

    async def list_datasets(
        self,
        limit: int = 100,
        offset: int = 0,
        is_based_on: Optional[str] = None,
        dataset_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List available datasets

        Args:
            limit: Maximum number of datasets to return (default 100)
            offset: Starting index for pagination
            is_based_on: Filter by population type (e.g., "UR" for Census 2021 Usual Residents)
            dataset_type: Filter by dataset type (e.g., "static")

        Returns:
            Dict with 'items' (list of datasets), 'total_count', 'limit', 'offset'
        """
        params: Dict[str, str] = {
            "limit": str(limit),
            "offset": str(offset),
        }
        if is_based_on:
            params["is_based_on"] = is_based_on
        if dataset_type:
            params["type"] = dataset_type

        return await self._request("/datasets", params)

    async def get_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """Get metadata for a specific dataset

        Args:
            dataset_id: Dataset identifier (e.g., "wellbeing-local-authority")

        Returns:
            Dataset metadata including title, description, contacts, links
        """
        return await self._request(f"/datasets/{dataset_id}")

    async def list_editions(self, dataset_id: str) -> Dict[str, Any]:
        """List editions for a dataset

        Args:
            dataset_id: Dataset identifier

        Returns:
            Dict with 'items' containing available editions
        """
        return await self._request(f"/datasets/{dataset_id}/editions")

    async def get_latest_version(self, dataset_id: str, edition: str = "time-series") -> Dict[str, Any]:
        """Get the latest version of a dataset edition

        Args:
            dataset_id: Dataset identifier
            edition: Edition name (default: "time-series")

        Returns:
            Version metadata including dimensions
        """
        return await self._request(f"/datasets/{dataset_id}/editions/{edition}/versions/latest")

    async def get_version(
        self, dataset_id: str, edition: str, version: int
    ) -> Dict[str, Any]:
        """Get a specific version of a dataset

        Args:
            dataset_id: Dataset identifier
            edition: Edition name
            version: Version number

        Returns:
            Version metadata including dimensions
        """
        return await self._request(f"/datasets/{dataset_id}/editions/{edition}/versions/{version}")

    # =========================================================================
    # Dimension Discovery
    # =========================================================================

    async def get_dimensions(self, dataset_id: str, edition: str, version: int) -> List[Dict[str, Any]]:
        """Get dimensions for a dataset version

        Args:
            dataset_id: Dataset identifier
            edition: Edition name
            version: Version number

        Returns:
            List of dimension objects with name, label, links
        """
        version_data = await self.get_version(dataset_id, edition, version)
        return version_data.get("dimensions", [])

    async def get_dimension_options(
        self,
        dataset_id: str,
        edition: str,
        version: int,
        dimension: str,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get available options for a dimension

        Args:
            dataset_id: Dataset identifier
            edition: Edition name
            version: Version number
            dimension: Dimension name (e.g., "geography", "time")
            limit: Maximum options to return

        Returns:
            Dict with 'items' containing dimension options
        """
        params = {"limit": str(limit)}
        return await self._request(
            f"/datasets/{dataset_id}/editions/{edition}/versions/{version}/dimensions/{dimension}/options",
            params,
        )

    # =========================================================================
    # Observations (Data Retrieval)
    # =========================================================================

    async def get_observations(
        self,
        dataset_id: str,
        edition: str = "time-series",
        version: str = "latest",
        dimensions: Optional[Dict[str, str]] = None,
        wildcard_dimension: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get observations from a dataset

        ONS API requires ALL dimensions to be specified. Use wildcard_dimension
        to specify which dimension should use "*" (only one allowed).

        Args:
            dataset_id: Dataset identifier
            edition: Edition name (default: "time-series")
            version: Version number or "latest"
            dimensions: Dict of dimension values (e.g., {"geography": "E08000026", "time": "2022-23"})
            wildcard_dimension: Name of dimension to use "*" wildcard for (only one allowed)

        Returns:
            Dict with observation data and metadata

        Example:
            # Get wellbeing for Coventry across all time periods
            await client.get_observations(
                "wellbeing-local-authority",
                dimensions={
                    "geography": "E08000026",
                    "estimate": "average-mean",
                    "measureofwellbeing": "life-satisfaction"
                },
                wildcard_dimension="time"
            )
        """
        # Get version info
        if version == "latest":
            version_info = await self.get_latest_version(dataset_id, edition)
            version = str(version_info.get("version", 1))

        endpoint = f"/datasets/{dataset_id}/editions/{edition}/versions/{version}/observations"

        # Build params - ONS API doesn't use "limit" for observations
        params: Dict[str, str] = {}
        if dimensions:
            for dim_name, dim_value in dimensions.items():
                params[dim_name] = dim_value

        # Add wildcard for specified dimension
        if wildcard_dimension:
            params[wildcard_dimension] = "*"

        return await self._request(endpoint, params, use_cache=False)

    async def get_dataset_dimensions_info(
        self,
        dataset_id: str,
        edition: str = "time-series",
        version: str = "latest",
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get dimension names and their available options

        Args:
            dataset_id: Dataset identifier
            edition: Edition name
            version: Version number or "latest"

        Returns:
            Dict mapping dimension names to their option lists
        """
        if version == "latest":
            version_info = await self.get_latest_version(dataset_id, edition)
            version = str(version_info.get("version", 1))

        # Get dimensions
        dims = await self.get_dimensions(dataset_id, edition, int(version))

        result: Dict[str, List[Dict[str, Any]]] = {}
        for dim in dims:
            dim_name = dim.get("name", "")
            if dim_name:
                try:
                    options = await self.get_dimension_options(
                        dataset_id, edition, int(version), dim_name, limit=50
                    )
                    result[dim_name] = options.get("items", [])
                except ONSAPIError:
                    result[dim_name] = []

        return result

    # =========================================================================
    # Convenience Methods for Common Use Cases
    # =========================================================================

    async def list_census_datasets(self, population_type: str = "UR") -> List[Dict[str, Any]]:
        """List Census 2021 datasets

        Args:
            population_type: Population type filter
                - "UR" = Usual Residents (default)
                - "HRP" = Household Reference Person
                - "HH" = Households

        Returns:
            List of Census dataset items
        """
        result = await self.list_datasets(limit=100, is_based_on=population_type)
        return result.get("items", [])

    async def list_local_authority_datasets(self) -> List[Dict[str, Any]]:
        """List datasets that include local authority level data

        Returns:
            List of datasets with local authority data
        """
        result = await self.list_datasets(limit=200)
        items = result.get("items", [])

        # Filter for local authority datasets
        la_datasets = []
        la_keywords = ["local-authority", "local authority", "lad", "region"]

        for item in items:
            item_id = item.get("id", "").lower()
            title = item.get("title", "").lower()
            desc = item.get("description", "").lower()

            if any(kw in item_id or kw in title or kw in desc for kw in la_keywords):
                la_datasets.append(item)

        return la_datasets

    async def get_data_for_area(
        self,
        dataset_id: str,
        area_code: str,
        time_period: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get data for a specific geographic area

        Args:
            dataset_id: Dataset identifier
            area_code: GSS code (e.g., "E08000026" for Coventry)
            time_period: Optional time filter

        Returns:
            Observations for the specified area
        """
        dimensions: Dict[str, str] = {"geography": area_code}
        if time_period:
            dimensions["time"] = time_period

        return await self.get_observations(dataset_id, dimensions=dimensions)

    async def search_datasets(self, query: str) -> List[Dict[str, Any]]:
        """Search datasets by keyword

        Args:
            query: Search term

        Returns:
            List of matching datasets
        """
        result = await self.list_datasets(limit=200)
        items = result.get("items", [])
        query_lower = query.lower()

        matches = []
        for item in items:
            title = item.get("title", "").lower()
            desc = item.get("description", "").lower()
            keywords = [k.lower() for k in item.get("keywords", [])]

            if (
                query_lower in title
                or query_lower in desc
                or any(query_lower in k for k in keywords)
            ):
                matches.append(item)

        return matches


class ONSAPIError(Exception):
    """Exception for ONS API errors"""

    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code

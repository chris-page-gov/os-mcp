import os
import aiohttp
import asyncio
import re
from typing import Dict, List, Any, Optional
from models import NGDAPIEndpoint, OpenAPISpecification, Collection, CollectionsCache
from .protocols import APIClient
from utils.logging_config import get_logger

logger = get_logger(__name__)


# TODO: We should add in the workflow context processing in here
class OSAPIClient(APIClient):
    """Implementation an OS API client"""

    user_agent = "os-ngd-mcp-server/1.0"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise the OS API client

        Args:
            api_key: Optional API key, if not provided will use OS_API_KEY env var
        """
        self.api_key = api_key
        self.session = None
        self.last_request_time = 0
        # TODO: This is because there seems to be some rate limiting in place - TBC if this is the case
        self.request_delay = 0.7
        self._cached_openapi_spec: Optional[OpenAPISpecification] = None
        self._cached_collections: Optional[CollectionsCache] = None

    async def _get_open_api_spec(self) -> OpenAPISpecification:
        """Get the OpenAPI spec for the OS NGD API"""
        try:
            response = await self.make_request("OPENAPI_SPEC", params={"f": "json"})
            spec = OpenAPISpecification(spec=response)
            return spec
        except Exception as e:
            raise ValueError(f"Failed to get OpenAPI spec: {e}")

    async def cache_openapi_spec(self) -> OpenAPISpecification:
        """
        Cache the OpenAPI spec.

        Returns:
            The cached OpenAPI spec
        """
        if self._cached_openapi_spec is None:
            logger.debug("Caching OpenAPI spec for LLM context...")
            try:
                self._cached_openapi_spec = await self._get_open_api_spec()
                logger.debug("OpenAPI spec successfully cached")
            except Exception as e:
                raise ValueError(f"Failed to cache OpenAPI spec: {e}")
        return self._cached_openapi_spec

    def _filter_latest_collections(
        self, collections: List[Dict[str, Any]]
    ) -> List[Collection]:
        """
        Filter collections to keep only the latest version of each collection type.
        For collections with IDs like 'trn-ntwk-roadlink-1', 'trn-ntwk-roadlink-2', 'trn-ntwk-roadlink-3',
        only keep the one with the highest number.

        Args:
            collections: Raw collections from API

        Returns:
            Filtered list of Collection objects
        """
        latest_versions: Dict[str, Dict[str, Any]] = {}

        for col in collections:
            col_id = col.get("id", "")

            match = re.match(r"^(.+?)-(\d+)$", col_id)

            if match:
                base_name = match.group(1)
                version_num = int(match.group(2))

                if (
                    base_name not in latest_versions
                    or version_num > latest_versions[base_name]["version"]
                ):
                    latest_versions[base_name] = {"version": version_num, "data": col}
            else:
                latest_versions[col_id] = {"version": 0, "data": col}

        filtered_collections = []
        for item in latest_versions.values():
            col_data = item["data"]
            filtered_collections.append(
                Collection(
                    id=col_data.get("id", ""),
                    title=col_data.get("title", ""),
                    description=col_data.get("description", ""),
                    links=col_data.get("links", []),
                    extent=col_data.get("extent", {}),
                    itemType=col_data.get("itemType", "feature"),
                )
            )

        return filtered_collections

    async def _get_collections(self) -> CollectionsCache:
        """Get all collections from the OS NGD API"""
        try:
            response = await self.make_request("COLLECTIONS")
            collections_list = response.get("collections", [])
            filtered = self._filter_latest_collections(collections_list)
            logger.debug(
                f"Filtered collections: {len(filtered)} collections"
            )  # Don't log the actual data
            return CollectionsCache(collections=filtered, raw_response=response)
        except Exception as e:
            sanitized_error = self._sanitise_api_key(str(e))
            logger.error(f"Error getting collections: {sanitized_error}")
            raise ValueError(f"Failed to get collections: {sanitized_error}")

    async def cache_collections(self) -> CollectionsCache:
        """
        Cache the collections data with filtering applied.

        Returns:
            The cached collections
        """
        if self._cached_collections is None:
            logger.debug("Caching collections for LLM context...")
            try:
                self._cached_collections = await self._get_collections()
                logger.debug(
                    f"Collections successfully cached - {len(self._cached_collections.collections)} collections after filtering"
                )
            except Exception as e:
                sanitized_error = self._sanitise_api_key(str(e))
                raise ValueError(f"Failed to cache collections: {sanitized_error}")
        return self._cached_collections

    async def initialise(self):
        """Initialise the aiohttp session if not already created"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(
                    force_close=True,
                    limit=1,  # TODO: Strict limit to only 1 connection - may need to revisit this
                )
            )

    async def close(self):
        """Close the session when done"""
        if self.session:
            await self.session.close()
            self.session = None
            self._cached_openapi_spec = None
            self._cached_collections = None

    async def get_api_key(self) -> str:
        """Get the OS API key from environment variable or init param."""
        if self.api_key:
            return self.api_key

        api_key = os.environ.get("OS_API_KEY")
        if not api_key:
            raise ValueError("OS_API_KEY environment variable is not set")
        return api_key

    def _sanitise_api_key(self, text: Any) -> str:
        """Remove API keys from any text (URLs, error messages, etc.)"""
        if not isinstance(text, str):
            return text

        patterns = [
            r"[?&]key=[^&\s]*",
            r"[?&]api_key=[^&\s]*",
            r"[?&]apikey=[^&\s]*",
            r"[?&]token=[^&\s]*",
        ]

        sanitized = text
        for pattern in patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        sanitized = re.sub(r"[?&]$", "", sanitized)
        sanitized = re.sub(r"&{2,}", "&", sanitized)
        sanitized = re.sub(r"\?&", "?", sanitized)

        return sanitized

    def _sanitise_response(self, data: Any) -> Any:
        """Remove API keys from response data recursively"""
        if isinstance(data, dict):
            sanitized_dict = {}
            for key, value in data.items():
                if isinstance(value, str) and any(
                    url_indicator in key.lower()
                    for url_indicator in ["href", "url", "link", "uri"]
                ):
                    sanitized_dict[key] = self._sanitise_api_key(value)
                elif isinstance(value, (dict, list)):
                    sanitized_dict[key] = self._sanitise_response(value)
                else:
                    sanitized_dict[key] = value
            return sanitized_dict
        elif isinstance(data, list):
            return [self._sanitise_response(item) for item in data]
        elif isinstance(data, str):
            if any(
                indicator in data
                for indicator in [
                    "http://",
                    "https://",
                    "key=",
                    "api_key=",
                    "apikey=",
                    "token=",
                ]
            ):
                return self._sanitise_api_key(data)

        return data

    async def make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        path_params: Optional[List[str]] = None,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """
        Make a request to the OS NGD API with proper error handling.

        Args:
            endpoint: Enum endpoint to use
            params: Additional query parameters
            path_params: Parameters to format into the URL path
            max_retries: Maximum number of retries for transient errors

        Returns:
            JSON response as dictionary
        """
        await self.initialise()

        if self.session is None:
            raise ValueError("Session not initialised")

        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.request_delay:
            await asyncio.sleep(self.request_delay - elapsed)

        try:
            endpoint_value = NGDAPIEndpoint[endpoint].value
        except KeyError:
            raise ValueError(f"Invalid endpoint: {endpoint}")

        if path_params:
            endpoint_value = endpoint_value.format(*path_params)

        api_key = await self.get_api_key()
        request_params = params or {}
        request_params["key"] = api_key

        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}

        client_ip = getattr(self.session, "_source_address", None)
        client_info = f" from {client_ip}" if client_ip else ""

        sanitized_url = self._sanitise_api_key(endpoint_value)
        logger.info(f"Requesting URL: {sanitized_url}{client_info}")

        for attempt in range(1, max_retries + 1):
            try:
                self.last_request_time = asyncio.get_event_loop().time()

                timeout = aiohttp.ClientTimeout(total=30.0)
                async with self.session.get(
                    endpoint_value,
                    params=request_params,
                    headers=headers,
                    timeout=timeout,
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        sanitized_error = self._sanitise_api_key(error_text)
                        error_message = (
                            f"HTTP Error: {response.status} - {sanitized_error}"
                        )
                        logger.error(f"Error: {error_message}")
                        raise ValueError(error_message)

                    response_data = await response.json()

                    return self._sanitise_response(response_data)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries:
                    sanitized_exception = self._sanitise_api_key(str(e))
                    error_message = f"Request failed after {max_retries} attempts: {sanitized_exception}"
                    logger.error(f"Error: {error_message}")
                    raise ValueError(error_message)
                else:
                    await asyncio.sleep(0.7)
            except Exception as e:
                sanitized_exception = self._sanitise_api_key(str(e))
                error_message = f"Request failed: {sanitized_exception}"
                logger.error(f"Error: {error_message}")
                raise ValueError(error_message)
        raise RuntimeError(
            "Unreachable: make_request exited retry loop without returning or raising"
        )

    async def make_request_no_auth(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 2,
    ) -> str:
        """
        Make a request without authentication (for public endpoints like documentation).

        Args:
            url: Full URL to request
            params: Additional query parameters
            max_retries: Maximum number of retries for transient errors

        Returns:
            Response text (not JSON parsed)
        """
        await self.initialise()

        if self.session is None:
            raise ValueError("Session not initialised")

        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.request_delay:
            await asyncio.sleep(self.request_delay - elapsed)

        request_params = params or {}
        headers = {"User-Agent": self.user_agent}

        logger.info(f"Requesting URL (no auth): {url}")

        for attempt in range(1, max_retries + 1):
            try:
                self.last_request_time = asyncio.get_event_loop().time()

                timeout = aiohttp.ClientTimeout(total=30.0)
                async with self.session.get(
                    url,
                    params=request_params,
                    headers=headers,
                    timeout=timeout,
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        error_message = f"HTTP Error: {response.status} - {error_text}"
                        logger.error(f"Error: {error_message}")
                        raise ValueError(error_message)

                    return await response.text()

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries:
                    error_message = (
                        f"Request failed after {max_retries} attempts: {str(e)}"
                    )
                    logger.error(f"Error: {error_message}")
                    raise ValueError(error_message)
                else:
                    await asyncio.sleep(0.7)
            except Exception as e:
                error_message = f"Request failed: {str(e)}"
                logger.error(f"Error: {error_message}")
                raise ValueError(error_message)

        raise RuntimeError(
            "Unreachable: make_request_no_auth exited retry loop without returning or raising"
        )

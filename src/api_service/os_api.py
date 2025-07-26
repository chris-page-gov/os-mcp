import os
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from enum import Enum
from .protocols import APIClient
from utils.logging_config import get_logger

logger = get_logger(__name__)


class NGDAPIEndpoint(Enum):
    """
    Enum for the OS API Endpoints following OGC API Features standard
    """

    # NGD Features Endpoints
    NGD_FEATURES_BASE_PATH = "https://api.os.uk/features/ngd/ofa/v1/{}"
    COLLECTIONS = NGD_FEATURES_BASE_PATH.format("collections")
    COLLECTION_INFO = NGD_FEATURES_BASE_PATH.format("collections/{}")
    COLLECTION_SCHEMA = NGD_FEATURES_BASE_PATH.format("collections/{}/schema")
    COLLECTION_FEATURES = NGD_FEATURES_BASE_PATH.format("collections/{}/items")
    COLLECTION_FEATURE_BY_ID = NGD_FEATURES_BASE_PATH.format("collections/{}/items/{}")
    COLLECTION_QUERYABLES = NGD_FEATURES_BASE_PATH.format("collections/{}/queryables")

    # OpenAPI Specification Endpoint
    OPENAPI_SPEC = NGD_FEATURES_BASE_PATH.format("api")

    # Linked Identifiers Endpoints
    LINKED_IDENTIFIERS_BASE_PATH = "https://api.os.uk/search/links/v1/{}"
    LINKED_IDENTIFIERS = LINKED_IDENTIFIERS_BASE_PATH.format("identifierTypes/{}/{}")

    # Places API Endpoints
    # PLACES_BASE_PATH = "https://api.os.uk/search/places/v1/{}"
    # PLACES_UPRN = PLACES_BASE_PATH.format("uprn")
    # POST_CODE = PLACES_BASE_PATH.format("postcode")


class OSAPIClient(APIClient):
    """Implementation of the OS APIs"""

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
        # Cache for OpenAPI spec
        self._cached_openapi_spec: Optional[Dict[str, Any]] = None

    async def get_open_api_spec(self):
        """Get the OpenAPI spec for the OS NGD API"""
        try:
            response = await self.make_request("OPENAPI_SPEC", params={"f": "json"})
            return response
        except Exception as e:
            logger.error(f"Error getting OpenAPI spec: {e}")
            raise e

    async def cache_openapi_spec(self) -> Dict[str, Any]:
        """
        Cache the OpenAPI spec during initialization.

        Returns:
            The cached OpenAPI spec
        """
        if self._cached_openapi_spec is None:
            logger.info("Caching OpenAPI spec for LLM context...")
            try:
                self._cached_openapi_spec = await self.get_open_api_spec()
                logger.info("OpenAPI spec successfully cached")
            except Exception as e:
                logger.error(f"Failed to cache OpenAPI spec: {e}")
                # Return a minimal spec if caching fails
                self._cached_openapi_spec = {
                    "error": "Failed to load OpenAPI spec",
                    "message": str(e),
                }
        return self._cached_openapi_spec

    def get_cached_openapi_spec(self) -> Optional[Dict[str, Any]]:
        """
        Get the cached OpenAPI spec.

        Returns:
            The cached OpenAPI spec or None if not cached yet
        """
        return self._cached_openapi_spec

    async def initialise(self):
        """Initialise the aiohttp session if not already created"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(
                    force_close=True,
                    limit=1,  # TODO: Strict limit to only 1 connection - may need to revisit this but don't know what the limits are for the OS API
                )
            )

    async def close(self):
        """Close the session when done"""
        if self.session:
            await self.session.close()
            self.session = None
            self._cached_openapi_spec = None

    def get_api_key(self) -> str:
        """Get the OS API key from environment variable or init param."""
        if self.api_key:
            return self.api_key

        api_key = os.environ.get("OS_API_KEY")
        if not api_key:
            raise ValueError("OS_API_KEY environment variable is not set")
        return api_key

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

        api_key = self.get_api_key()
        request_params = params or {}
        request_params["key"] = api_key

        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}

        client_ip = getattr(self.session, "_source_address", None)
        client_info = f" from {client_ip}" if client_ip else ""

        logger.info(f"Requesting URL: {endpoint_value}{client_info}")

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
                        error_message = (
                            f"HTTP Error: {response.status} - {await response.text()}"
                        )
                        logger.error(f"Error: {error_message}")
                        raise ValueError(error_message)

                    return await response.json()
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
            "Unreachable: make_request exited retry loop without returning or raising"
        )

import os
import sys
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from enum import Enum

from .protocols import APIClient


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

    # Linked Identifiers Endpoints
    LINKED_IDENTIFIERS_BASE_PATH = "https://api.os.uk/search/links/v1/{}"
    LINKED_IDENTIFIERS = LINKED_IDENTIFIERS_BASE_PATH.format("identifierTypes/{}/{}")

    # Places API Endpoints
    PLACES_BASE_PATH = "https://api.os.uk/search/places/v1/{}"
    PLACES_UPRN = PLACES_BASE_PATH.format("uprn")

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
        # Ensure session is initialised
        await self.initialise()

        if self.session is None:
            raise ValueError("Session not initialised")

        # Rate limiting
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.request_delay:
            await asyncio.sleep(self.request_delay - elapsed)

        # Get the endpoint from the enum
        try:
            endpoint_value = NGDAPIEndpoint[endpoint].value
        except KeyError:
            raise ValueError(f"Invalid endpoint: {endpoint}")

        # Format path parameters if provided
        if path_params:
            endpoint_value = endpoint_value.format(*path_params)

        # Add API key to parameters
        api_key = self.get_api_key()
        request_params = params or {}
        request_params["key"] = api_key

        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}

        print(
            f"Requesting URL: {endpoint_value} with params: {request_params}",
            file=sys.stderr,
        )

        for attempt in range(1, max_retries + 1):
            try:
                # Record request time just before making the request
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
                        print(f"Error: {error_message}", file=sys.stderr)
                        raise ValueError(error_message)

                    return await response.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries:
                    error_message = (
                        f"Request failed after {max_retries} attempts: {str(e)}"
                    )
                    print(f"Error: {error_message}", file=sys.stderr)
                    raise ValueError(error_message)
                else:
                    await asyncio.sleep(0.7)
            except Exception as e:
                error_message = f"Request failed: {str(e)}"
                print(f"Error: {error_message}", file=sys.stderr)
                raise ValueError(error_message)
        raise RuntimeError(
            "Unreachable: make_request exited retry loop without returning or raising"
        )

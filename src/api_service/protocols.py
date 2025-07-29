from typing import Protocol, Dict, List, Any, Optional, runtime_checkable


@runtime_checkable
class APIClient(Protocol):
    """Protocol for API clients"""

    async def initialise(self):
        """Initialise the aiohttp session if not already created"""
        ...

    async def close(self):
        """Close the aiohttp session"""
        ...

    async def get_api_key(self) -> str:
        """Get the API key"""
        ...

    async def make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        path_params: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Make a request to an API endpoint"""
        ...

    async def cache_openapi_spec(self):
        """Cache the OpenAPI spec"""
        ...
    
    async def cache_collections(self):
        """Cache the collections data"""
        ...
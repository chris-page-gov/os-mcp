from typing import Optional, List
from api_service.protocols import APIClient
from .protocols import MCPService, FeatureService
import json
import asyncio


class OSNGDService(FeatureService):
    """Implementation of the OS NGD API service with MCP"""

    def __init__(self, api_client: APIClient, mcp_service: MCPService):
        """
        Initialise the OS NGD service

        Args:
            api_client: API client implementation
            mcp_service: MCP service implementation
        """
        self.api_client = api_client
        self.mcp = mcp_service

        # Register tools
        self.register_tools()

    def register_tools(self) -> None:
        """Register all MCP tools"""
        self.hello_world = self.mcp.tool()(self.hello_world)
        self.check_api_key = self.mcp.tool()(self.check_api_key)
        self.list_collections = self.mcp.tool()(self.list_collections)
        self.get_collection_info = self.mcp.tool()(self.get_collection_info)
        self.get_collection_queryables = self.mcp.tool()(self.get_collection_queryables)
        self.search_features = self.mcp.tool()(self.search_features)
        self.get_feature = self.mcp.tool()(self.get_feature)
        self.get_linked_identifiers = self.mcp.tool()(self.get_linked_identifiers)
        self.get_bulk_features = self.mcp.tool()(self.get_bulk_features)
        self.get_bulk_linked_features = self.mcp.tool()(self.get_bulk_linked_features)
        self.get_prompt_templates = self.mcp.tool()(self.get_prompt_templates)
        self.search_by_uprn = self.mcp.tool()(self.search_by_uprn)

    def hello_world(self) -> str:
        """A simple test tool that returns a greeting message."""
        return "Hello from the OS NGD - Features API MCP server! The connection is working correctly."

    def check_api_key(self) -> str:
        """Check if the OS API key is available."""
        try:
            self.api_client.get_api_key()
            return "OS_API_KEY is set!"
        except ValueError as e:
            return str(e)

    async def list_collections(self) -> str:
        """
        List all available feature collections in the OS NGD API.

        Returns:
            JSON string with collection info (id, title only)
        """
        try:
            data = await self.api_client.make_request("COLLECTIONS")

            if not data or "collections" not in data:
                return json.dumps({"error": "No collections found"})

            collections = [
                {"id": col.get("id"), "title": col.get("title")}
                for col in data.get("collections", [])
            ]

            return json.dumps({"collections": collections})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def get_collection_info(self, collection_id: str) -> str:
        """
        Get detailed information about a specific collection.

        Args:
            collection_id: The collection ID

        Returns:
            JSON string with collection information
        """
        try:
            data = await self.api_client.make_request(
                "COLLECTION_INFO", path_params=[collection_id]
            )

            return json.dumps(data)
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def get_collection_queryables(self, collection_id: str) -> str:
        """
        Get the list of queryable properties for a collection.

        Args:
            collection_id: The collection ID

        Returns:
            JSON string with queryable properties
        """
        try:
            data = await self.api_client.make_request(
                "COLLECTION_QUERYABLES", path_params=[collection_id]
            )

            return json.dumps(data)
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def search_features(
        self,
        collection_id: str,
        bbox: Optional[str] = None,
        crs: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        query_attr: Optional[str] = None,
        query_attr_value: Optional[str] = None,
    ) -> str:
        """
        Search for features in a collection with simplified parameters.
        """
        try:
            params = {}

            # Add standard parameters
            if limit:
                params["limit"] = limit
            if offset:
                params["offset"] = offset

            # Add spatial parameters
            if bbox:
                params["bbox"] = bbox
            if crs:
                params["crs"] = crs

            # Add query attribute filter
            if query_attr and query_attr_value:
                params["filter"] = f"{query_attr}={query_attr_value}"

            data = await self.api_client.make_request(
                "COLLECTION_FEATURES", params=params, path_params=[collection_id]
            )

            return json.dumps(data)
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def get_feature(
        self, collection_id: str, feature_id: str, crs: Optional[str] = None
    ) -> str:
        """
        Get a specific feature by ID.

        Args:
            collection_id: The collection ID
            feature_id: The feature ID
            crs: Coordinate reference system for the response

        Returns:
            JSON string with feature data
        """
        try:
            params = {}
            if crs:
                params["crs"] = crs

            data = await self.api_client.make_request(
                "COLLECTION_FEATURE_BY_ID",
                params=params,
                path_params=[collection_id, feature_id],
            )

            return json.dumps(data)
        except Exception as e:
            return json.dumps({"error": f"Error getting feature: {str(e)}"})

    async def get_linked_identifiers(
        self, identifier_type: str, identifier: str, feature_type: Optional[str] = None
    ) -> str:
        """
        Get linked identifiers for a specified identifier.

        Args:
            identifier_type: The type of identifier (e.g., 'TOID', 'UPRN')
            identifier: The identifier value
            feature_type: Optional feature type to filter results

        Returns:
            JSON string with linked identifiers or filtered results
        """
        try:
            data = await self.api_client.make_request(
                "LINKED_IDENTIFIERS", path_params=[identifier_type, identifier]
            )

            # If no feature_type filter, return raw data
            if not feature_type:
                return json.dumps(data)

            # Filter by feature type
            identifiers = []
            if "correlations" in data and isinstance(data["correlations"], list):
                for item in data["correlations"]:
                    if item.get("correlatedFeatureType") == feature_type:
                        if "correlatedIdentifiers" in item and isinstance(
                            item["correlatedIdentifiers"], list
                        ):
                            identifiers = [
                                id_obj["identifier"]
                                for id_obj in item["correlatedIdentifiers"]
                                if isinstance(id_obj, dict) and "identifier" in id_obj
                            ]
                            break

            return json.dumps({"identifiers": identifiers})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def get_bulk_features(
        self,
        collection_id: str,
        identifiers: List[str],
        query_by_attr: Optional[str] = None,
    ) -> str:
        """
        Get multiple features in a single call.

        Args:
            collection_id: The collection ID
            identifiers: List of feature IDs or attribute values
            query_by_attr: If provided, query by this attribute instead of feature ID

        Returns:
            JSON string with features data
        """
        try:
            tasks = []

            for identifier in identifiers:
                if query_by_attr:
                    # Query by attribute
                    tasks.append(
                        self.search_features(
                            collection_id,
                            query_attr=query_by_attr,
                            query_attr_value=identifier,
                        )
                    )
                else:
                    # Query by feature ID
                    tasks.append(self.get_feature(collection_id, feature_id=identifier))

            results = await asyncio.gather(*tasks)

            # Parse results back to objects for processing
            parsed_results = [json.loads(result) for result in results]

            return json.dumps({"results": parsed_results})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def get_bulk_linked_features(
        self,
        identifier_type: str,
        identifiers: List[str],
        feature_type: Optional[str] = None,
    ) -> str:
        """
        Get linked features for multiple identifiers in a single call.

        Args:
            identifier_type: The type of identifier (e.g., 'TOID', 'UPRN')
            identifiers: List of identifier values
            feature_type: Optional feature type to filter results

        Returns:
            JSON string with linked features data
        """
        try:
            tasks = [
                self.get_linked_identifiers(identifier_type, identifier, feature_type)
                for identifier in identifiers
            ]

            results = await asyncio.gather(*tasks)

            # Parse results back to objects
            parsed_results = [json.loads(result) for result in results]

            return json.dumps({"results": parsed_results})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def get_prompt_templates(self, category: Optional[str] = None) -> str:
        """
        Get standard prompt templates for interacting with this service.

        Args:
            category: Optional category of templates to return
                     (general, collections, features, linked_identifiers)

        Returns:
            JSON string containing prompt templates
        """
        from promp_templates.prompt_templates import PROMPT_TEMPLATES

        if category and category in PROMPT_TEMPLATES:
            return json.dumps({category: PROMPT_TEMPLATES[category]})

        return json.dumps(PROMPT_TEMPLATES)

    async def search_by_uprn(
        self, 
        uprn: int, 
        format: str = "JSON", 
        dataset: str = "DPA",
        lr: str = "EN",
        output_srs: str = "EPSG:27700",
        fq: Optional[List[str]] = None
    ) -> str:
        """
        Find addresses by UPRN using the OS Places API.
        
        Args:
            uprn: A valid UPRN (Unique Property Reference Number)
            format: The format the response will be returned in (JSON or XML)
            dataset: The dataset to return (DPA, LPI or both separated by comma)
            lr: Language of addresses to return (EN, CY)
            output_srs: The output spatial reference system
            fq: Optional filter for classification code, logical status code, etc.
            
        Returns:
            JSON string with matched addresses
        """
        try:
            params = {
                "uprn": uprn,
                "format": format,
                "dataset": dataset,
                "lr": lr,
                "output_srs": output_srs
            }
            
            # Add filters if provided
            if fq:
                params["fq"] = fq
            
            data = await self.api_client.make_request(
                "PLACES_UPRN",
                params=params
            )
            
            return json.dumps(data)
        except Exception as e:
            return json.dumps({"error": f"Error searching by UPRN: {str(e)}"})

    def run(self) -> None:
        """Run the MCP service"""
        self.mcp.run()

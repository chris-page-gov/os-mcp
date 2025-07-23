import json
import asyncio
import os

from typing import Optional, List, Dict, Any, Union, cast
from api_service.protocols import APIClient
from .protocols import MCPService, FeatureService
from .guardrails import ToolGuardrails
from utils.logging_config import get_logger
from mcp.server.fastmcp import Context

logger = get_logger(__name__)


class OSDataHubService(FeatureService):
    """Implementation of the OS NGD API service with MCP"""

    def __init__(self, api_client: APIClient, mcp_service: MCPService, stdio_middleware=None):
        """
        Initialise the OS NGD service

        Args:
            api_client: API client implementation
            mcp_service: MCP service implementation
            stdio_middleware: Optional STDIO middleware for rate limiting
        """
        self.api_client = api_client
        self.mcp = mcp_service
        self.stdio_middleware = stdio_middleware
        
        self.guardrails = ToolGuardrails()
        
        self.register_tools()

    def register_tools(self) -> None:
        """Register all MCP tools with guardrails and optional STDIO middleware"""
        
        def apply_middleware(func):
            """Apply both guardrails and STDIO middleware if available"""
            wrapped = self.guardrails.basic_guardrails(func)
            
            if self.stdio_middleware:
                wrapped = self.stdio_middleware.require_auth_and_rate_limit(wrapped)
            
            return wrapped

        self.hello_world = self.mcp.tool()(apply_middleware(self.hello_world))
        self.check_api_key = self.mcp.tool()(apply_middleware(self.check_api_key))
        self.list_collections = self.mcp.tool()(apply_middleware(self.list_collections))
        self.get_collection_info = self.mcp.tool()(apply_middleware(self.get_collection_info))
        self.get_collection_queryables = self.mcp.tool()(apply_middleware(self.get_collection_queryables))
        self.search_features = self.mcp.tool()(apply_middleware(self.search_features))
        self.get_feature = self.mcp.tool()(apply_middleware(self.get_feature))
        self.get_linked_identifiers = self.mcp.tool()(apply_middleware(self.get_linked_identifiers))
        self.get_bulk_features = self.mcp.tool()(apply_middleware(self.get_bulk_features))
        self.get_bulk_linked_features = self.mcp.tool()(apply_middleware(self.get_bulk_linked_features))
        self.get_prompt_templates = self.mcp.tool()(apply_middleware(self.get_prompt_templates))
        self.search_by_uprn = self.mcp.tool()(apply_middleware(self.search_by_uprn))
        self.search_by_post_code = self.mcp.tool()(apply_middleware(self.search_by_post_code))

    async def hello_world(self, name: str) -> str:
        """Simple hello world tool for testing"""
        return f"Hello, {name}! 👋"

    def check_api_key(self) -> str:
        """Check if the OS API key is available."""
        try:
            self.api_client.get_api_key()
            return "OS_API_KEY is set!"
        except ValueError as e:
            return str(e)

    async def list_collections(
        self,
    ) -> str:
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

    async def get_collection_info(
        self,
        collection_id: str,
    ) -> str:
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

    async def get_collection_queryables(
        self,
        collection_id: str,
    ) -> str:
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
            params: Dict[str, Union[str, int]] = {}

            if limit:
                params["limit"] = limit
            if offset:
                params["offset"] = offset

            if bbox:
                params["bbox"] = bbox
            if crs:
                params["crs"] = crs

            if query_attr and query_attr_value:
                params["filter"] = f"{query_attr}={query_attr_value}"

            data = await self.api_client.make_request(
                "COLLECTION_FEATURES", params=params, path_params=[collection_id]
            )

            return json.dumps(data)
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def get_feature(
        self,
        collection_id: str,
        feature_id: str,
        crs: Optional[str] = None,
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
            params: Dict[str, str] = {}
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
        self,
        identifier_type: str,
        identifier: str,
        feature_type: Optional[str] = None,
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

            if not feature_type:
                return json.dumps(data)

            identifiers: List[str] = []
            if "correlations" in data:
                assert isinstance(data["correlations"], list), (
                    "correlations must be a list"
                )
                correlations = cast(List[Dict[str, Any]], data["correlations"])
                for item in correlations:
                    if item.get("correlatedFeatureType") == feature_type:
                        if "correlatedIdentifiers" in item and isinstance(
                            item["correlatedIdentifiers"], list
                        ):
                            correlated_ids = cast(
                                List[Dict[str, Any]], item["correlatedIdentifiers"]
                            )
                            identifiers = [
                                id_obj["identifier"]
                                for id_obj in correlated_ids
                                if "identifier" in id_obj
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
            tasks: List[Any] = []

            for identifier in identifiers:
                if query_by_attr:
                    tasks.append(
                        self.search_features(
                            collection_id,
                            query_attr=query_by_attr,
                            query_attr_value=identifier,
                        )
                    )
                else:
                    tasks.append(self.get_feature(collection_id, feature_id=identifier))

            results: List[str] = await asyncio.gather(*tasks)

            parsed_results: List[Dict[str, Any]] = [
                json.loads(result) for result in results
            ]

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

            parsed_results = [json.loads(result) for result in results]

            return json.dumps({"results": parsed_results})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def get_prompt_templates(
        self,
        category: Optional[str] = None,
    ) -> str:
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
        uprn: str,
        format: str = "JSON",
        dataset: str = "DPA",
        lr: str = "EN",
        output_srs: str = "EPSG:27700",
        fq: Optional[List[str]] = None,
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
            # Validate all parameters first
            errors = self._validate_uprn_params(
                uprn, format, dataset, lr, output_srs, fq
            )
            if errors:
                return json.dumps({"error": errors})

            # Convert UPRN to integer
            uprn_int = int(uprn)

            params = {
                "uprn": uprn_int,
                "format": format,
                "dataset": dataset,
                "lr": lr,
                "output_srs": output_srs,
            }

            if fq:
                params["fq"] = ",".join(fq)

            data = await self.api_client.make_request("PLACES_UPRN", params=params)

            # Return sanitized data as JSON
            return json.dumps(data)
        except Exception as e:
            return json.dumps({"error": f"Error searching by UPRN: {str(e)}"})

    def _validate_uprn_params(
        self,
        uprn: str,
        format: str,
        dataset: str,
        lr: str,
        output_srs: str,
        fq: Optional[List[str]],
    ) -> Optional[str]:
        """Validate all parameters for the UPRN search and return error message if invalid."""
        errors: List[str] = []

        def check(condition: bool, error_msg: str) -> None:
            if condition:
                errors.append(error_msg)

        # Check each parameter
        check(not uprn.isdigit(), "UPRN must contain only digits")
        check(format not in ["JSON", "XML"], "Format must be 'JSON' or 'XML'")

        valid_datasets = ["DPA", "LPI"]
        dataset_parts = dataset.split(",")
        check(
            not all(part.strip() in valid_datasets for part in dataset_parts),
            "Dataset must be 'DPA', 'LPI', or both comma-separated",
        )

        check(lr not in ["EN", "CY"], "Language must be 'EN' or 'CY'")
        check(output_srs not in ["EPSG:27700"], "Output SRS must be 'EPSG:27700'")
        check(
            fq is not None and len(fq) == 0,
            "Filters cannot be an empty list",
        )

        return errors[0] if errors else None

    async def search_by_post_code(
        self,
        postcode: str,
        format: str = "JSON",
        dataset: str = "DPA",
        lr: str = "EN",
        output_srs: str = "EPSG:27700",
        fq: Optional[List[str]] = None,
    ) -> str:
        """
        Find addresses by POSTCODE using the OS Places API.

        Args:
            postcode: A valid POSTCODE (e.g. "SW1A 1AA")
            format: The format the response will be returned in (JSON or XML)
            dataset: The dataset to return (DPA, LPI or both separated by comma)
            lr: Language of addresses to return (EN, CY)
            output_srs: The output spatial reference system
            fq: Optional filter for classification code, logical status code, etc.

        Returns:
            JSON string with matched addresses
        """
        try:
            errors = self._validate_post_code_params(
                postcode, format, dataset, lr, output_srs, fq
            )
            if errors:
                return json.dumps({"error": errors})

            params = {
                "postcode": postcode,
                "format": format,
                "dataset": dataset,
                "lr": lr,
                "output_srs": output_srs,
            }

            if fq:
                params["fq"] = ",".join(fq)

            data = await self.api_client.make_request("POST_CODE", params=params)

            return json.dumps(data)
        except Exception as e:
            return json.dumps({"error": f"Error searching by POSTCODE: {str(e)}"})

    def _validate_post_code_params(
        self,
        postcode: str,
        format: str,
        dataset: str,
        lr: str,
        output_srs: str,
        fq: Optional[List[str]],
    ) -> Optional[str]:
        """Validate all parameters for the POSTCODE search and return error message if invalid."""
        errors: List[str] = []

        def check(condition: bool, error_msg: str) -> None:
            if condition:
                errors.append(error_msg)

        check(not postcode.isalnum(), "POSTCODE must contain only letters and numbers")
        check(format not in ["JSON", "XML"], "Format must be 'JSON' or 'XML'")

        valid_datasets = ["DPA", "LPI"]
        dataset_parts = dataset.split(",")
        check(
            not all(part.strip() in valid_datasets for part in dataset_parts),
            "Dataset must be 'DPA', 'LPI', or both comma-separated",
        )

        check(lr not in ["EN", "CY"], "Language must be 'EN' or 'CY'")
        check(output_srs not in ["EPSG:27700"], "Output SRS must be 'EPSG:27700'")
        check(
            fq is not None and len(fq) == 0,
            "Filters must be provided as a list",
        )

        return errors[0] if errors else None


    def run(self) -> None:
        """Run the MCP service"""
        self.mcp.run()

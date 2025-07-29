"""
Types for the OS NGD API MCP Server
"""

from enum import Enum
from pydantic import BaseModel
from typing import Any, List, Dict


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


class OpenAPISpecification(BaseModel):
    """OpenAPI specification for the OS NGD API"""

    spec: dict[str, Any]


class WorkflowStep(BaseModel):
    """A single step in a workflow plan"""

    step_number: int
    description: str
    api_endpoint: str
    parameters: Dict[str, Any]
    dependencies: List[int] = []


class WorkflowPlan(BaseModel):
    """Generated workflow plan for user requests"""

    user_request: str
    steps: List[WorkflowStep]
    reasoning: str
    estimated_complexity: str = "simple"


class Collection(BaseModel):
    """Represents a feature collection from the OS NGD API"""

    id: str
    title: str
    description: str = ""
    links: List[Dict[str, Any]] = []
    extent: Dict[str, Any] = {}
    itemType: str = "feature"


class CollectionsCache(BaseModel):
    """Cached collections data with filtering applied"""

    collections: List[Collection]
    raw_response: Dict[str, Any]

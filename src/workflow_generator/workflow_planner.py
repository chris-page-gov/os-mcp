from typing import Dict, Any, Optional
from models import OpenAPISpecification
from utils.logging_config import get_logger

logger = get_logger(__name__)


class WorkflowPlanner:
    """Simple context provider for LLM workflow planning"""
    
    def __init__(self, openapi_spec: Optional[OpenAPISpecification], collections_info: Optional[Dict[str, Any]] = None):
        self.spec = openapi_spec
        self.collections_info = collections_info or {}
    
    def get_context(self) -> Dict[str, Any]:
        """Get context for LLM to plan its own workflow"""
        return {
            "available_collections": self.collections_info,
            "openapi_endpoints": list(self.spec.spec.get("paths", {}).keys()) if self.spec else [],
        }

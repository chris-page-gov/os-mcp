import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from utils.logging_config import get_logger

logger = get_logger(__name__)

REQUEST_ID_HEADER = "x-request-id"

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Injects a request ID into every incoming HTTP request for traceability."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        logger.debug(f"Request {request_id} {request.method} {request.url.path}")
        return response

"""FraudDNA Request Correlation Middleware.

Generates and propagates unique request and correlation identifiers across
asynchronous request flows, attaches identifiers to response headers, and
binds them to structured logging contextvars.
"""

import re
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings
from app.core.logging import clear_request_context, set_request_context

# Strict character set and length boundaries for incoming correlation identifiers
SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


def is_safe_identifier(value: str | None) -> bool:
    """Validate that incoming header value is bounded and contains only safe characters."""
    if not value or not isinstance(value, str):
        return False
    return bool(SAFE_ID_PATTERN.match(value.strip()))


def generate_request_id() -> str:
    """Generate a clean, collision-resistant request identifier."""
    return f"req_{uuid.uuid4().hex[:16]}"


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware establishing request and correlation identifiers for every HTTP request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Check for client-provided identifiers
        incoming_req_id = request.headers.get(settings.REQUEST_ID_HEADER)
        incoming_corr_id = request.headers.get(settings.CORRELATION_ID_HEADER)

        # Adopt incoming ID only if safe, otherwise generate fresh identifier
        request_id = (
            incoming_req_id.strip()
            if (incoming_req_id and is_safe_identifier(incoming_req_id))
            else generate_request_id()
        )
        correlation_id = (
            incoming_corr_id.strip()
            if (incoming_corr_id and is_safe_identifier(incoming_corr_id))
            else request_id
        )

        # Store in request state and task contextvars
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        set_request_context(request_id=request_id, correlation_id=correlation_id)

        try:
            response: Response = await call_next(request)
            # Propagate correlation headers back to client
            response.headers[settings.REQUEST_ID_HEADER] = request_id
            response.headers[settings.CORRELATION_ID_HEADER] = correlation_id
            return response
        finally:
            clear_request_context()

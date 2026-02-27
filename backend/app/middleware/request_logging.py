"""
Request Logging Middleware

Logs every HTTP request with timing, status, and metadata
in structured JSON format for observability.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Structured request/response logging."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        # Attach request ID
        request.state.request_id = request_id

        # Process request
        response: Response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log (skip health checks to reduce noise)
        if request.url.path != "/health":
            logger.info(
                "request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", ""),
                    "tenant_id": getattr(request.state, "organization_id", None),
                },
            )

        # Add response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response

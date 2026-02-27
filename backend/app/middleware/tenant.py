"""
Tenant Isolation Middleware

Extracts organization context from JWT token and injects
into request state for downstream tenant-scoped queries.
"""

import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.security import decode_token

logger = logging.getLogger(__name__)

# Paths that don't require tenant context
EXEMPT_PATHS = {
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
}


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Extracts tenant (organization_id) from JWT and attaches to request.state.

    All downstream handlers can access request.state.organization_id
    to scope database queries to the authenticated tenant.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip tenant extraction for exempt paths
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # Default: no tenant context
        request.state.organization_id = None
        request.state.user_id = None
        request.state.user_role = None

        # Try to extract from Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = decode_token(token)
            if payload:
                request.state.organization_id = payload.get("org_id")
                request.state.user_id = payload.get("sub")
                request.state.user_role = payload.get("role")

        response = await call_next(request)
        return response

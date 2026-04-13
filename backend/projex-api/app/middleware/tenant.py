"""Tenant middleware: extract tenant from JWT / subdomain, set search_path."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.security import decode_token

# Paths that don't require tenant context
_PUBLIC_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


class TenantMiddleware(BaseHTTPMiddleware):
    """Resolve tenant from JWT token or subdomain and store on request.state."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip tenant resolution for public paths
        if request.url.path in _PUBLIC_PATHS:
            request.state.tenant_slug = None
            return await call_next(request)

        tenant_slug = None

        # 1. Try JWT token (preferred)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
            try:
                payload = decode_token(token)
                tenant_slug = payload.get("tenant_id")
            except Exception:
                pass

        # 2. Fallback to subdomain (e.g., acme.projex.id)
        if not tenant_slug:
            host = request.headers.get("host", "")
            parts = host.split(".")
            if len(parts) >= 3:
                candidate = parts[0]
                if candidate not in ("www", "api", "app"):
                    tenant_slug = candidate

        request.state.tenant_slug = tenant_slug
        return await call_next(request)

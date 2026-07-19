"""Attach baseline security headers to every HTTP response."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.services.enterprise_security.api_security import secure_headers


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        # Do not override CORS Access-Control-* already set by CORSMiddleware.
        for key, value in secure_headers().items():
            if key.lower().startswith("access-control-"):
                continue
            # Allow static media caching; keep API responses no-store.
            if key == "Cache-Control" and request.url.path.startswith("/media/"):
                continue
            response.headers.setdefault(key, value)
        return response

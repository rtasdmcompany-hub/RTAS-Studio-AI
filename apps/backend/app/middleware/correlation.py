"""Attach correlation / request IDs for log and trace continuity."""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        incoming = (
            (request.headers.get("X-Correlation-Id") or "").strip()
            or (request.headers.get("X-Request-Id") or "").strip()
        )
        correlation_id = incoming or uuid.uuid4().hex
        request.state.correlation_id = correlation_id
        request.state.request_id = correlation_id
        response = await call_next(request)
        response.headers["X-Correlation-Id"] = correlation_id
        response.headers.setdefault("X-Request-Id", correlation_id)
        return response

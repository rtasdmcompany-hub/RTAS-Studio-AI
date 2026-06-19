"""
HTTP middleware — content moderation gate for video generation routes.
"""

from __future__ import annotations

import json
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.schemas.generation import GenerateRequest
from app.services.content_moderation import (
    CONTENT_POLICY_MESSAGE,
    log_content_policy_violation,
    moderate_generate_request,
)

logger = logging.getLogger(__name__)

GENERATION_POST_PATHS = frozenset({"/api/generate", "/api/generate/"})


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


class ContentModerationMiddleware(BaseHTTPMiddleware):
    """Block POST /api/generate before route handlers when policy is violated."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if request.method != "POST" or path not in GENERATION_POST_PATHS:
            return await call_next(request)

        body_bytes = await request.body()
        try:
            payload = json.loads(body_bytes.decode("utf-8"))
            body = GenerateRequest.model_validate(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            return await call_next(request)

        result = moderate_generate_request(body)
        if not result.allowed:
            log_content_policy_violation(
                user_id=body.user_id,
                device_fingerprint=body.device_fingerprint,
                ip_address=_client_ip(request),
                category=body.category,
                job_id=body.job_id,
                matched_terms=list(result.matched_terms),
                reason="Middleware blocked generation request",
                route=path,
                preview_only=body.preview_only,
            )
            return JSONResponse(
                status_code=403,
                content={"detail": CONTENT_POLICY_MESSAGE},
            )

        async def receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        replay_request = Request(request.scope, receive)
        return await call_next(replay_request)

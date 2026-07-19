"""Centralized service-to-service auth for FastAPI routes."""

from __future__ import annotations

import hmac

from fastapi import Header, HTTPException

from app.core.config import settings
from app.core.runtime import is_production


def require_backend_secret(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
) -> None:
    """
    Validate X-Rtas-Backend-Secret.

    Production: AI_BACKEND_SECRET must be configured and match (fail closed).
    Development: if secret unset, allow (local tooling); if set, must match.
    """
    expected = (settings.ai_backend_secret or "").strip()
    provided = (x_rtas_backend_secret or "").strip()

    if not expected:
        if is_production():
            raise HTTPException(
                status_code=503,
                detail="AI_BACKEND_SECRET is required in production",
            )
        return

    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")

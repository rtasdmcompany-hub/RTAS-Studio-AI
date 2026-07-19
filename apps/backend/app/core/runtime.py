"""Runtime environment helpers for production fail-closed security."""

from __future__ import annotations

import os


def is_production() -> bool:
    """True when running on Vercel or an explicitly production RTAS/ENV flag."""
    if (os.environ.get("VERCEL") or "").strip() == "1":
        return True
    env = (os.environ.get("RTAS_ENV") or os.environ.get("ENVIRONMENT") or "").strip().lower()
    if env in {"production", "prod"}:
        return True
    if (os.environ.get("NODE_ENV") or "").strip().lower() == "production":
        return True
    return False


def openapi_enabled() -> bool:
    """OpenAPI/Swagger UI — disabled in production unless explicitly forced on."""
    force = (os.environ.get("RTAS_ENABLE_OPENAPI") or "").strip().lower()
    if force in {"1", "true", "yes"}:
        return True
    if force in {"0", "false", "no"}:
        return False
    return not is_production()

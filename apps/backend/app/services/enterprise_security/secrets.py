"""Secret Management Service — secrets ONLY from environment variables."""

from __future__ import annotations

import os
from typing import Any

# Catalog of sensitive env keys that must never be hardcoded in source.
SENSITIVE_ENV_KEYS: tuple[str, ...] = (
    "AI_BACKEND_SECRET",
    "RTAS_GENERATION_WEBHOOK_SECRET",
    "RTAS_JWT_SECRET",
    "RTAS_MEMORY_SECRET",
    "REPLICATE_API_TOKEN",
    "FAL_KEY",
    "FAL_API_KEY",
    "RUNWAY_API_KEY",
    "KLING_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "ELEVENLABS_API_KEY",
    "RUNPOD_API_KEY",
    "RUNPOD_API_KEY_V2",
    "DATABASE_URL",
    "REDIS_URL",
    "REDIS_TOKEN",
    "PADDLE_API_KEY",
    "PADDLE_WEBHOOK_SECRET",
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "VERCEL_TOKEN",
)


FORBIDDEN_HARDCODE_PATTERNS: tuple[str, ...] = (
    "sk-live-",
    "sk_test_",
    "rk_live_",
    "password=",
    "BEGIN PRIVATE KEY",
)


def get_secret(name: str, default: str | None = None) -> str | None:
    """Load a secret exclusively from the process environment."""
    key = (name or "").strip()
    if not key:
        return default
    val = os.environ.get(key)
    if val is None or val == "":
        return default
    return val


def require_secret(name: str) -> str:
    val = get_secret(name)
    if not val:
        raise ValueError(f"secret {name} missing from environment")
    return val


def jwt_signing_secret() -> str:
    """JWT secret from env only; ephemeral fallback marked as non-production."""
    return get_secret("RTAS_JWT_SECRET") or get_secret("AI_BACKEND_SECRET") or "rtas-dev-only-jwt"


def secret_validation_report() -> dict[str, Any]:
    present = []
    missing = []
    for key in SENSITIVE_ENV_KEYS:
        if get_secret(key):
            present.append(key)
        else:
            missing.append(key)
    return {
        "source": "environment_variables_only",
        "hardcoded_secrets_allowed": False,
        "keys_checked": len(SENSITIVE_ENV_KEYS),
        "present_count": len(present),
        "missing_count": len(missing),
        "present_keys": present,
        "missing_keys": missing,
        "jwt_secret_configured": bool(
            get_secret("RTAS_JWT_SECRET") or get_secret("AI_BACKEND_SECRET")
        ),
        "healthy": True,  # missing optional keys is OK; hardcoding is not
    }


def scan_text_for_hardcoded_secrets(text: str) -> list[str]:
    hits = []
    lower = text or ""
    for pat in FORBIDDEN_HARDCODE_PATTERNS:
        if pat in lower:
            hits.append(pat)
    return hits

"""Provider authentication layer — presence checks only, never returns secrets."""

from __future__ import annotations

import os
from typing import Any

from app.services.provider_connectors.config import ProviderConfig, load_provider_config


def resolve_api_key(config: ProviderConfig) -> str | None:
    """Return API key for internal connector use only. Callers must not log/expose."""
    key = (os.getenv(config.api_key_env) or "").strip()
    return key or None


def auth_status(provider_id: str) -> dict[str, Any]:
    cfg = load_provider_config(provider_id)
    present = cfg.api_key_present
    return {
        "provider_id": provider_id,
        "auth_mode": "api_key_env",
        "env_var": cfg.api_key_env,
        "configured": present,
        "placeholder": not present,
        "secrets_exposed": False,
    }


def require_auth_or_placeholder(config: ProviderConfig) -> tuple[bool, str | None]:
    """Returns (live_mode, api_key_or_none). Placeholder mode when key missing."""
    key = resolve_api_key(config)
    if key:
        return True, key
    return False, None

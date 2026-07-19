"""Env-backed signing secrets — refuse weak defaults in production."""

from __future__ import annotations

import os

from app.core.runtime import is_production


def _resolve(env_keys: tuple[str, ...], *, dev_fallback: str) -> str:
    for key in env_keys:
        val = (os.environ.get(key) or "").strip()
        if val:
            return val
    # Prefer shared backend secret when dedicated key unset
    shared = (os.environ.get("AI_BACKEND_SECRET") or "").strip()
    if shared:
        return shared
    if is_production():
        raise ValueError(
            f"Missing signing secret ({'/'.join(env_keys)} or AI_BACKEND_SECRET) in production"
        )
    return dev_fallback


def public_api_hash_secret() -> str:
    return _resolve(("RTAS_PUBLIC_API_HASH_SECRET",), dev_fallback="rtas-public-api-key-v1")


def plugin_signing_secret() -> str:
    return _resolve(("RTAS_PLUGIN_SIGNING_SECRET",), dev_fallback="rtas-plugin-signing-v1")


def automation_webhook_secret() -> str:
    return _resolve(
        ("RTAS_AUTOMATION_WEBHOOK_SECRET",),
        dev_fallback="rtas-automation-webhook-v1",
    )


def export_signing_secret() -> bytes:
    return _resolve(
        ("RTAS_EXPORT_SIGNING_SECRET",),
        dev_fallback="rtas-export-sim-signing-key-v1",
    ).encode("utf-8")


def asset_library_signing_secret() -> bytes:
    return _resolve(
        ("RTAS_ASSET_LIBRARY_SIGNING_SECRET",),
        dev_fallback="rtas-asset-library-signing-key-v1",
    ).encode("utf-8")

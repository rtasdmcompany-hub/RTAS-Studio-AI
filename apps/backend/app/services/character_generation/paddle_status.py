"""Paddle production configuration verification — env vars only, never expose secrets."""

from __future__ import annotations

import os
from typing import Any

# Exact env variable names — values never returned.
PADDLE_ENV_KEYS = (
    "NEXT_PUBLIC_PAYMENT_PROVIDER",
    "PADDLE_WEBHOOK_SECRET",
    "NEXT_PUBLIC_PADDLE_CLIENT_TOKEN",
    "NEXT_PUBLIC_PADDLE_CHECKOUT_URL",
    "NEXT_PUBLIC_PADDLE_TESTER_CHECKOUT_URL",
    "NEXT_PUBLIC_PADDLE_STANDARD_CHECKOUT_URL",
    "NEXT_PUBLIC_PADDLE_PREMIUM_CHECKOUT_URL",
    "PADDLE_TESTER_PRICE_ID",
    "PADDLE_STANDARD_PRICE_ID",
    "PADDLE_PREMIUM_PRICE_ID",
    "RTAS_DEFER_PADDLE",
)

_CRITICAL = (
    "PADDLE_WEBHOOK_SECRET",
    "NEXT_PUBLIC_PADDLE_CLIENT_TOKEN",
)


def _present(name: str) -> bool:
    value = (os.environ.get(name) or "").strip()
    return bool(value)


def paddle_status() -> dict[str, Any]:
    """Return configuration status without any secret values."""
    provider = (os.environ.get("NEXT_PUBLIC_PAYMENT_PROVIDER") or "paddle").strip().lower()
    defer = (os.environ.get("RTAS_DEFER_PADDLE") or "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    presence = {key: _present(key) for key in PADDLE_ENV_KEYS}
    critical_ok = all(presence[k] for k in _CRITICAL)
    configured = provider == "paddle" and (critical_ok or defer)
    return {
        "provider": provider,
        "configured": configured,
        "deferred": defer,
        "critical_keys_present": critical_ok,
        "env_presence": presence,
        "secrets_exposed": False,
        "message": (
            "paddle-ready"
            if critical_ok
            else (
                "paddle-deferred-until-keys"
                if defer
                else "paddle-keys-incomplete"
            )
        ),
    }


def assert_no_secrets_in_payload(payload: dict[str, Any]) -> bool:
    blob = str(payload).lower()
    banned = (
        "pdl_",
        "whsec_",
        "paddle_webhook_secret=",
        "next_public_paddle_client_token=",
    )
    # Presence flags are OK; raw secret-looking values are not
    if "secrets_exposed" in blob and "true" in blob.split("secrets_exposed")[-1][:20]:
        return False
    return not any(b in blob and "true" != b for b in banned if len(b) > 5)

"""API Security Layer — rate limit, validation, sanitize, signature, CSRF, CORS, headers, replay."""

from __future__ import annotations

import hashlib
import hmac
import re
import time
from typing import Any
from urllib.parse import urlparse

from app.services.enterprise_security import store
from app.services.enterprise_security.secrets import get_secret
from app.services.enterprise_security.version import (
    DEFAULT_RATE_LIMIT_PER_MINUTE,
    REPLAY_WINDOW_SEC,
)

_DANGEROUS_RE = re.compile(
    r"(?i)(<script|javascript:|onerror\s*=|union\s+select|--\s*$|\bdrop\s+table\b)"
)


class ApiSecurityError(ValueError):
    pass


def sanitize_input(value: str, *, max_len: int = 8000) -> str:
    text = (value or "").strip()
    if len(text) > max_len:
        text = text[:max_len]
    text = text.replace("\x00", "")
    if _DANGEROUS_RE.search(text):
        raise ApiSecurityError("input failed sanitization")
    return text


def validate_request_payload(payload: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ApiSecurityError("payload must be an object")
    for key in required or []:
        if key not in payload or payload[key] in (None, ""):
            raise ApiSecurityError(f"missing required field: {key}")
    clean: dict[str, Any] = {}
    for k, v in payload.items():
        if isinstance(v, str):
            clean[k] = sanitize_input(v)
        else:
            clean[k] = v
    return clean


def check_rate_limit(actor_key: str, *, limit: int | None = None) -> None:
    allowed = store.rate_hit(
        actor_key,
        time.time(),
        int(limit or DEFAULT_RATE_LIMIT_PER_MINUTE),
        60.0,
    )
    if not allowed:
        raise ApiSecurityError("rate limit exceeded")


def validate_api_signature(
    *,
    body: str,
    signature: str,
    timestamp: str | None = None,
) -> bool:
    secret = get_secret("AI_BACKEND_SECRET") or get_secret("RTAS_JWT_SECRET")
    if not secret:
        # Dev mode: accept when secret unset but still require non-empty signature shape
        return bool(signature) and len(signature) >= 16
    msg = f"{timestamp or ''}.{body or ''}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, (signature or "").lower()):
        raise ApiSecurityError("invalid API signature")
    return True


def validate_csrf(token: str | None, session_token: str | None) -> bool:
    if not session_token:
        return True  # CSRF applies to cookie/session flows
    if not token:
        raise ApiSecurityError("CSRF token required")
    expected = hashlib.sha256(f"csrf:{session_token}".encode()).hexdigest()[:32]
    if not hmac.compare_digest(expected, token):
        raise ApiSecurityError("invalid CSRF token")
    return True


def csrf_token_for_session(session_token: str) -> str:
    return hashlib.sha256(f"csrf:{session_token}".encode()).hexdigest()[:32]


def validate_cors_origin(origin: str | None, allowed: list[str] | None = None) -> bool:
    if not origin:
        return True
    allow = allowed or [
        o.strip()
        for o in (get_secret("CORS_ORIGINS") or "http://localhost:3000").split(",")
        if o.strip()
    ]
    if origin in allow or "*" in allow:
        return True
    # Allow same registrable host for vercel preview if configured
    host = urlparse(origin).netloc
    if any(urlparse(a).netloc == host for a in allow):
        return True
    raise ApiSecurityError(f"CORS origin not allowed: {origin}")


def secure_headers() -> dict[str, str]:
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "X-XSS-Protection": "0",
        "Cache-Control": "no-store",
        "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }


def check_replay_protection(nonce: str, *, timestamp: str | None = None) -> bool:
    now = time.time()
    if timestamp:
        try:
            ts = float(timestamp)
        except ValueError as exc:
            raise ApiSecurityError("invalid replay timestamp") from exc
        if abs(now - ts) > REPLAY_WINDOW_SEC:
            raise ApiSecurityError("replay timestamp outside window")
    if not nonce or len(nonce) < 8:
        raise ApiSecurityError("replay nonce required")
    if not store.check_replay(nonce, now, float(REPLAY_WINDOW_SEC)):
        raise ApiSecurityError("replay detected")
    return True

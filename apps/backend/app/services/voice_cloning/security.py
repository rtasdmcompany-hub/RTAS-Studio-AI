"""Security — ownership, authz, signed requests, audit (no provider secrets)."""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass, field
from typing import Any


_AUDIT: list[dict[str, Any]] = []
_MAX_AUDIT = 5000


@dataclass
class AuthContext:
    owner_id: str | None
    authenticated: bool
    roles: list[str] = field(default_factory=list)
    request_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_id": self.owner_id,
            "authenticated": self.authenticated,
            "roles": list(self.roles),
            "request_id": self.request_id,
        }


def build_auth_context(
    *,
    owner_id: str | None,
    backend_secret_ok: bool,
    roles: list[str] | None = None,
    request_id: str | None = None,
) -> AuthContext:
    return AuthContext(
        owner_id=(owner_id or "").strip() or None,
        authenticated=bool(backend_secret_ok),
        roles=list(roles or ["voice_clone"]),
        request_id=request_id,
    )


def assert_ownership(resource_owner: str | None, actor: AuthContext) -> None:
    """Raise PermissionError if actor cannot access resource."""
    if not actor.authenticated and actor.owner_id is None:
        # Dev mode without secret + no owner: open
        return
    if "admin" in actor.roles:
        return
    if resource_owner is None:
        return
    if actor.owner_id and actor.owner_id == resource_owner:
        return
    raise PermissionError("Voice ownership validation failed")


def sign_payload(payload: str, secret: str, *, ts: int | None = None) -> str:
    """HMAC signature for request integrity. Never logs the secret."""
    if not secret:
        return ""
    timestamp = int(ts if ts is not None else time.time())
    msg = f"{timestamp}.{payload}".encode()
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={sig}"


def verify_signature(payload: str, signature: str, secret: str, *, max_age_sec: int = 300) -> bool:
    if not secret:
        return True  # unsigned allowed when no secret configured
    if not signature:
        return False
    parts = dict(
        p.split("=", 1) for p in signature.split(",") if "=" in p
    )
    ts_s = parts.get("t")
    sig = parts.get("v1")
    if not ts_s or not sig:
        return False
    try:
        ts = int(ts_s)
    except ValueError:
        return False
    if abs(int(time.time()) - ts) > max_age_sec:
        return False
    expected = sign_payload(payload, secret, ts=ts)
    return hmac.compare_digest(expected, f"t={ts},v1={sig}")


def audit_log(
    action: str,
    *,
    clone_id: str | None = None,
    character_id: str | None = None,
    owner_id: str | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = {
        "action": action,
        "clone_id": clone_id,
        "character_id": character_id,
        "owner_id": owner_id,
        "ts": time.time(),
        "detail": dict(detail or {}),
        # Never include provider credentials
        "provider_secret_exposed": False,
    }
    _AUDIT.append(entry)
    while len(_AUDIT) > _MAX_AUDIT:
        _AUDIT.pop(0)
    return entry


def list_audit(limit: int = 50) -> list[dict[str, Any]]:
    return list(_AUDIT[-limit:])


def clear_audit() -> None:
    _AUDIT.clear()

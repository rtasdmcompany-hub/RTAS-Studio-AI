"""JWT, session, API key, and service account authentication."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from app.services.enterprise_security import store
from app.services.enterprise_security.models import AuthMethod, Principal, Role, new_id
from app.services.enterprise_security.secrets import jwt_signing_secret
from app.services.enterprise_security.version import JWT_TTL_SEC


class AuthError(PermissionError):
    pass


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def issue_jwt(
    *,
    subject: str,
    role: Role = "user",
    scopes: list[str] | None = None,
    team_id: str | None = None,
    ttl_sec: int | None = None,
) -> dict[str, Any]:
    now = int(time.time())
    ttl = int(ttl_sec or JWT_TTL_SEC)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "role": role,
        "scopes": scopes or [],
        "team_id": team_id,
        "iat": now,
        "exp": now + ttl,
        "jti": new_id("jti"),
    }
    h = _b64url(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    secret = jwt_signing_secret().encode("utf-8")
    sig = _b64url(hmac.new(secret, f"{h}.{p}".encode(), hashlib.sha256).digest())
    token = f"{h}.{p}.{sig}"
    principal = Principal(
        principal_id=new_id("prin"),
        role=role,
        auth_method="jwt",
        subject=subject,
        scopes=list(scopes or []),
        team_id=team_id,
        expires_at=str(payload["exp"]),
    )
    return {"token": token, "principal": principal.to_dict(), "expires_in": ttl}


def validate_jwt(token: str) -> Principal:
    try:
        h, p, s = token.split(".")
    except ValueError as exc:
        raise AuthError("malformed JWT") from exc
    secret = jwt_signing_secret().encode("utf-8")
    expected = _b64url(hmac.new(secret, f"{h}.{p}".encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, s):
        raise AuthError("invalid JWT signature")
    payload = json.loads(_b64url_decode(p))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise AuthError("JWT expired")
    return Principal(
        principal_id=str(payload.get("jti") or new_id("prin")),
        role=payload.get("role") or "user",
        auth_method="jwt",
        subject=str(payload.get("sub") or ""),
        scopes=list(payload.get("scopes") or []),
        team_id=payload.get("team_id"),
        expires_at=str(payload.get("exp")),
    )


def create_session(
    *,
    subject: str,
    role: Role = "user",
    scopes: list[str] | None = None,
    team_id: str | None = None,
) -> dict[str, Any]:
    token = new_id("sess")
    principal = Principal(
        principal_id=new_id("prin"),
        role=role,
        auth_method="session",
        subject=subject,
        scopes=list(scopes or []),
        team_id=team_id,
    )
    store.save_session(token, principal)
    return {"session_token": token, "principal": principal.to_dict()}


def validate_session(token: str) -> Principal:
    principal = store.get_session(token)
    if not principal:
        raise AuthError("invalid session")
    return principal


def logout_session(token: str) -> None:
    store.delete_session(token)


def register_api_key(
    *,
    api_key: str,
    subject: str,
    role: Role = "user",
    scopes: list[str] | None = None,
) -> dict[str, Any]:
    if not api_key or len(api_key) < 16:
        raise AuthError("API key too short")
    key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    principal = Principal(
        principal_id=new_id("prin"),
        role=role,
        auth_method="api_key",
        subject=subject,
        scopes=list(scopes or ["api"]),
    )
    store.save_api_key(key_hash, principal)
    return {"ok": True, "key_fingerprint": key_hash[:12], "principal": principal.to_dict()}


def validate_api_key(api_key: str) -> Principal:
    key_hash = hashlib.sha256((api_key or "").encode("utf-8")).hexdigest()
    principal = store.get_api_key(key_hash)
    if not principal:
        raise AuthError("invalid API key")
    return principal


def register_service_account(
    *,
    account_id: str,
    role: Role = "service",
    scopes: list[str] | None = None,
) -> dict[str, Any]:
    principal = Principal(
        principal_id=new_id("prin"),
        role=role if role == "service" else "service",
        auth_method="service_account",
        subject=account_id,
        scopes=list(scopes or ["service"]),
    )
    store.save_service_account(account_id, principal)
    return {"ok": True, "principal": principal.to_dict()}


def validate_service_account(account_id: str, service_token: str) -> Principal:
    """Service account validated via registered id + env-backed shared secret compare."""
    from app.services.enterprise_security.secrets import get_secret

    expected = get_secret("AI_BACKEND_SECRET") or get_secret("RTAS_JWT_SECRET")
    if expected and not hmac.compare_digest(expected, service_token or ""):
        raise AuthError("invalid service account token")
    principal = store.get_service_account(account_id)
    if not principal:
        # auto-register ephemeral service principal when secret matches
        if not expected:
            raise AuthError("service account not registered")
        reg = register_service_account(account_id=account_id)
        return Principal(**reg["principal"])
    return principal


def authenticate(
    *,
    method: AuthMethod,
    credential: str,
    subject: str | None = None,
) -> Principal:
    if method == "jwt":
        return validate_jwt(credential)
    if method == "session":
        return validate_session(credential)
    if method == "api_key":
        return validate_api_key(credential)
    if method == "service_account":
        if not subject:
            raise AuthError("service account subject required")
        return validate_service_account(subject, credential)
    raise AuthError(f"unsupported auth method: {method}")

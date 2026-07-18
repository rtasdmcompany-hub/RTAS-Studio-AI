"""Session creation, validation, and revocation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Any

from app.services.enterprise_auth import store
from app.services.enterprise_auth.errors import SessionInvalidError, UnauthorizedError
from app.services.enterprise_auth.models import Session, new_id
from app.services.enterprise_auth.version import (
    DEFAULT_SESSION_TTL_SEC,
    MAX_SESSIONS_PER_USER,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def create_session(
    *,
    user_id: str,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    team_id: str | None = None,
    role_key: str | None = None,
    auth_provider: str = "credentials",
    sso_provider: str | None = None,
    ttl_sec: int = DEFAULT_SESSION_TTL_SEC,
    metadata: dict[str, Any] | None = None,
) -> Session:
    if not user_id or not str(user_id).strip():
        raise UnauthorizedError("userId is required for session")
    existing = store.list_sessions_for_user(user_id)
    active = [s for s in existing if s.status == "active"]
    if len(active) >= MAX_SESSIONS_PER_USER:
        # Revoke oldest active session
        oldest = sorted(active, key=lambda s: s.created_at)[0]
        store.revoke_session(oldest.id)
    now = _now()
    session = Session(
        id=new_id("sess_"),
        user_id=str(user_id).strip(),
        organization_id=organization_id,
        workspace_id=workspace_id,
        team_id=team_id,
        role_key=role_key,
        token=token_urlsafe(32),
        auth_provider=auth_provider,
        sso_provider=sso_provider,
        expires_at=now + timedelta(seconds=max(60, ttl_sec)),
        created_at=now,
        last_seen_at=now,
        metadata=dict(metadata or {}),
    )
    return store.save_session(session)


def validate_session(token: str | None) -> Session:
    if not token or not str(token).strip():
        raise SessionInvalidError("session token is required")
    session = store.get_session_by_token(str(token).strip())
    if session is None:
        raise SessionInvalidError("session not found")
    if session.status != "active":
        raise SessionInvalidError(f"session is {session.status}")
    if _ensure_aware(session.expires_at) < _now():
        session.status = "expired"
        store.save_session(session)
        raise SessionInvalidError("session expired")
    session.last_seen_at = _now()
    store.save_session(session)
    return session


def revoke_session(token: str | None = None, *, session_id: str | None = None) -> Session:
    session: Session | None = None
    if session_id:
        session = store.get_session(session_id)
    elif token:
        session = store.get_session_by_token(str(token).strip())
    if session is None:
        raise SessionInvalidError("session not found")
    revoked = store.revoke_session(session.id)
    assert revoked is not None
    return revoked


def get_session(session_id: str) -> Session | None:
    return store.get_session(session_id)

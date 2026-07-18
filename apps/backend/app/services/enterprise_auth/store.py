"""Thread-safe store for sessions and auth audit events."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

from app.services.enterprise_auth.version import MAX_AUDIT_EVENTS

if TYPE_CHECKING:
    from app.services.enterprise_auth.models import AuthAuditEvent, Session

_lock = threading.RLock()
_sessions: OrderedDict[str, "Session"] = OrderedDict()
_token_index: dict[str, str] = {}
_audits: OrderedDict[str, "AuthAuditEvent"] = OrderedDict()


def reset_store() -> None:
    with _lock:
        _sessions.clear()
        _token_index.clear()
        _audits.clear()


def save_session(session: "Session") -> "Session":
    with _lock:
        _sessions[session.id] = session
        if session.token:
            _token_index[session.token] = session.id
        return session


def get_session(session_id: str) -> "Session | None":
    with _lock:
        return _sessions.get(session_id)


def get_session_by_token(token: str) -> "Session | None":
    with _lock:
        sid = _token_index.get(token)
        return _sessions.get(sid) if sid else None


def list_sessions_for_user(user_id: str) -> list["Session"]:
    with _lock:
        return [s for s in _sessions.values() if s.user_id == user_id]


def revoke_session(session_id: str) -> "Session | None":
    with _lock:
        session = _sessions.get(session_id)
        if session is None:
            return None
        session.status = "revoked"
        return session


def add_audit(event: "AuthAuditEvent") -> "AuthAuditEvent":
    with _lock:
        _audits[event.id] = event
        while len(_audits) > MAX_AUDIT_EVENTS:
            _audits.popitem(last=False)
        return event


def list_audits(
    *,
    limit: int = 50,
    organization_id: str | None = None,
    event_type: str | None = None,
) -> list["AuthAuditEvent"]:
    with _lock:
        items = list(_audits.values())
    items.reverse()
    if organization_id:
        items = [e for e in items if e.organization_id == organization_id]
    if event_type:
        items = [e for e in items if e.event_type == event_type]
    return items[: max(1, min(limit, 500))]


def stats() -> dict[str, int]:
    with _lock:
        active = sum(1 for s in _sessions.values() if s.status == "active")
        return {
            "sessions": len(_sessions),
            "activeSessions": active,
            "auditEvents": len(_audits),
        }

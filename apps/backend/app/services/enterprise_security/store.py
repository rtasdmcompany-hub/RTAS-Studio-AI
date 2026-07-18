"""Thread-safe security / audit / compliance store."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.enterprise_security.models import (
        AccessLogEntry,
        AuditLogEntry,
        ComplianceReport,
        Principal,
        SecurityEvent,
        SecurityPolicy,
    )

_lock = threading.Lock()
_audits: list["AuditLogEntry"] = []
_events: list["SecurityEvent"] = []
_access: list["AccessLogEntry"] = []
_policies: OrderedDict[str, "SecurityPolicy"] = OrderedDict()
_reports: list["ComplianceReport"] = []
_sessions: dict[str, "Principal"] = {}
_api_keys: dict[str, "Principal"] = {}
_service_accounts: dict[str, "Principal"] = {}
_consents: dict[str, dict] = {}
_replay_nonces: OrderedDict[str, float] = OrderedDict()
_rate_buckets: dict[str, list[float]] = {}
_MAX = 8000


def add_audit(entry: "AuditLogEntry") -> None:
    with _lock:
        _audits.append(entry)
        if len(_audits) > _MAX:
            del _audits[:1000]


def audits(limit: int = 50, action: str | None = None) -> list["AuditLogEntry"]:
    with _lock:
        items = [a for a in _audits if not action or a.action == action]
        return list(reversed(items[-max(1, min(500, limit)) :]))


def add_event(entry: "SecurityEvent") -> None:
    with _lock:
        _events.append(entry)
        if len(_events) > _MAX:
            del _events[:1000]


def events(limit: int = 50, severity: str | None = None) -> list["SecurityEvent"]:
    with _lock:
        items = [e for e in _events if not severity or e.severity == severity]
        return list(reversed(items[-max(1, min(500, limit)) :]))


def add_access(entry: "AccessLogEntry") -> None:
    with _lock:
        _access.append(entry)
        if len(_access) > _MAX:
            del _access[:1000]


def access_logs(limit: int = 50) -> list["AccessLogEntry"]:
    with _lock:
        return list(reversed(_access[-max(1, min(500, limit)) :]))


def save_policy(policy: "SecurityPolicy") -> "SecurityPolicy":
    with _lock:
        _policies[policy.policy_id] = policy
        return policy


def all_policies() -> list["SecurityPolicy"]:
    with _lock:
        return list(_policies.values())


def add_report(report: "ComplianceReport") -> None:
    with _lock:
        _reports.append(report)
        if len(_reports) > 500:
            del _reports[:100]


def reports(limit: int = 20) -> list["ComplianceReport"]:
    with _lock:
        return list(reversed(_reports[-max(1, min(100, limit)) :]))


def save_session(token: str, principal: "Principal") -> None:
    with _lock:
        _sessions[token] = principal


def get_session(token: str) -> "Principal | None":
    with _lock:
        return _sessions.get(token)


def delete_session(token: str) -> None:
    with _lock:
        _sessions.pop(token, None)


def save_api_key(key_hash: str, principal: "Principal") -> None:
    with _lock:
        _api_keys[key_hash] = principal


def get_api_key(key_hash: str) -> "Principal | None":
    with _lock:
        return _api_keys.get(key_hash)


def save_service_account(account_id: str, principal: "Principal") -> None:
    with _lock:
        _service_accounts[account_id] = principal


def get_service_account(account_id: str) -> "Principal | None":
    with _lock:
        return _service_accounts.get(account_id)


def set_consent(user_id: str, payload: dict) -> None:
    with _lock:
        _consents[user_id] = payload


def get_consent(user_id: str) -> dict | None:
    with _lock:
        return _consents.get(user_id)


def consent_count() -> int:
    with _lock:
        return len(_consents)


def check_replay(nonce: str, now: float, window: float) -> bool:
    """Return True if nonce is fresh (allowed). False if replay."""
    with _lock:
        # purge old
        cutoff = now - window
        while _replay_nonces:
            k, t = next(iter(_replay_nonces.items()))
            if t >= cutoff:
                break
            _replay_nonces.popitem(last=False)
        if nonce in _replay_nonces:
            return False
        _replay_nonces[nonce] = now
        while len(_replay_nonces) > 5000:
            _replay_nonces.popitem(last=False)
        return True


def rate_hit(key: str, now: float, limit: int, window: float = 60.0) -> bool:
    """Return True if allowed, False if rate limited."""
    with _lock:
        bucket = _rate_buckets.setdefault(key, [])
        cutoff = now - window
        _rate_buckets[key] = [t for t in bucket if t >= cutoff]
        if len(_rate_buckets[key]) >= limit:
            return False
        _rate_buckets[key].append(now)
        return True


def clear() -> None:
    with _lock:
        _audits.clear()
        _events.clear()
        _access.clear()
        _policies.clear()
        _reports.clear()
        _sessions.clear()
        _api_keys.clear()
        _service_accounts.clear()
        _consents.clear()
        _replay_nonces.clear()
        _rate_buckets.clear()

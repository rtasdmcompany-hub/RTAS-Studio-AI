"""Thread-safe in-memory store for licenses, API keys, rate limits, webhooks."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.license_platform.models import (
        ApiKey,
        ApiUsageRecord,
        License,
        LicenseHistoryEntry,
        PersonalAccessToken,
        RateLimitState,
        Webhook,
        WebhookDelivery,
    )

_lock = threading.RLock()

_licenses: OrderedDict[str, "License"] = OrderedDict()
_license_by_org: dict[str, str] = {}
_license_by_key: dict[str, str] = {}
_license_history: OrderedDict[str, "LicenseHistoryEntry"] = OrderedDict()
_api_keys: OrderedDict[str, "ApiKey"] = OrderedDict()
_key_by_hash: dict[str, str] = {}
_pats: OrderedDict[str, "PersonalAccessToken"] = OrderedDict()
_pat_by_hash: dict[str, str] = {}
_usage: OrderedDict[str, "ApiUsageRecord"] = OrderedDict()
_rate_states: dict[tuple[str, str], "RateLimitState"] = {}
_webhooks: OrderedDict[str, "Webhook"] = OrderedDict()
_deliveries: OrderedDict[str, "WebhookDelivery"] = OrderedDict()

_api_timings: list[float] = []
_api_count = 0
_error_count = 0


def reset_store() -> None:
    global _api_count, _error_count
    with _lock:
        _licenses.clear()
        _license_by_org.clear()
        _license_by_key.clear()
        _license_history.clear()
        _api_keys.clear()
        _key_by_hash.clear()
        _pats.clear()
        _pat_by_hash.clear()
        _usage.clear()
        _rate_states.clear()
        _webhooks.clear()
        _deliveries.clear()
        _api_timings.clear()
        _api_count = 0
        _error_count = 0


def record_error() -> None:
    global _error_count
    with _lock:
        _error_count += 1


@contextmanager
def timed_op() -> Iterator[None]:
    global _api_count
    start = time.perf_counter()
    try:
        yield
    except Exception:
        record_error()
        raise
    finally:
        ms = (time.perf_counter() - start) * 1000
        with _lock:
            _api_timings.append(ms)
            if len(_api_timings) > 500:
                del _api_timings[: len(_api_timings) - 500]
            _api_count += 1


def metrics() -> dict[str, Any]:
    with _lock:
        timings = list(_api_timings)
        avg = sum(timings) / len(timings) if timings else 0.0
        return {
            "apiCount": _api_count,
            "errorCount": _error_count,
            "avgLatencyMs": round(avg, 3),
            "licenses": len(_licenses),
            "licenseHistory": len(_license_history),
            "apiKeys": len(_api_keys),
            "personalAccessTokens": len(_pats),
            "usageRecords": len(_usage),
            "rateLimitStates": len(_rate_states),
            "webhooks": len(_webhooks),
            "webhookDeliveries": len(_deliveries),
        }


# --- Licenses ---


def save_license(lic: "License") -> None:
    with _lock:
        _licenses[lic.id] = lic
        _license_by_org[lic.organization_id] = lic.id
        _license_by_key[lic.license_key.upper()] = lic.id


def get_license(license_id: str) -> "License | None":
    with _lock:
        return _licenses.get(license_id)


def get_license_by_org(organization_id: str) -> "License | None":
    with _lock:
        lid = _license_by_org.get(organization_id)
        return _licenses.get(lid) if lid else None


def get_license_by_key(license_key: str) -> "License | None":
    with _lock:
        lid = _license_by_key.get((license_key or "").strip().upper())
        return _licenses.get(lid) if lid else None


def save_license_history(entry: "LicenseHistoryEntry") -> None:
    with _lock:
        _license_history[entry.id] = entry


def list_license_history(
    organization_id: str, *, limit: int = 100
) -> list["LicenseHistoryEntry"]:
    with _lock:
        items = [
            h for h in _license_history.values() if h.organization_id == organization_id
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


# --- API keys ---


def save_api_key(key: "ApiKey") -> None:
    with _lock:
        _api_keys[key.id] = key
        if key.key_hash:
            _key_by_hash[key.key_hash] = key.id


def get_api_key(key_id: str) -> "ApiKey | None":
    with _lock:
        return _api_keys.get(key_id)


def get_api_key_by_hash(key_hash: str) -> "ApiKey | None":
    with _lock:
        kid = _key_by_hash.get(key_hash)
        return _api_keys.get(kid) if kid else None


def drop_key_hash(key_hash: str) -> None:
    with _lock:
        _key_by_hash.pop(key_hash, None)


def list_api_keys(
    organization_id: str,
    *,
    owner_user_id: str | None = None,
    workspace_id: str | None = None,
    include_inactive: bool = True,
    limit: int = 100,
) -> list["ApiKey"]:
    with _lock:
        items = [
            k
            for k in _api_keys.values()
            if k.organization_id == organization_id
            and (owner_user_id is None or k.owner_user_id == owner_user_id)
            and (workspace_id is None or k.workspace_id == workspace_id)
            and (include_inactive or k.active)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


# --- Personal access tokens ---


def save_pat(pat: "PersonalAccessToken") -> None:
    with _lock:
        _pats[pat.id] = pat
        if pat.token_hash:
            _pat_by_hash[pat.token_hash] = pat.id


def get_pat(pat_id: str) -> "PersonalAccessToken | None":
    with _lock:
        return _pats.get(pat_id)


def get_pat_by_hash(token_hash: str) -> "PersonalAccessToken | None":
    with _lock:
        pid = _pat_by_hash.get(token_hash)
        return _pats.get(pid) if pid else None


def list_pats(user_id: str, *, limit: int = 100) -> list["PersonalAccessToken"]:
    with _lock:
        items = [p for p in _pats.values() if p.user_id == user_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


# --- Usage ---


def save_usage(rec: "ApiUsageRecord") -> None:
    with _lock:
        _usage[rec.id] = rec
        if len(_usage) > 50_000:
            _usage.popitem(last=False)


def list_usage(
    organization_id: str, *, api_key_id: str | None = None, limit: int = 1000
) -> list["ApiUsageRecord"]:
    with _lock:
        items = [
            u
            for u in _usage.values()
            if u.organization_id == organization_id
            and (api_key_id is None or u.api_key_id == api_key_id)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


# --- Rate limit state ---


def get_rate_state(scope: str, scope_id: str) -> "RateLimitState | None":
    with _lock:
        return _rate_states.get((scope, scope_id))


def save_rate_state(state: "RateLimitState") -> None:
    with _lock:
        _rate_states[(state.scope, state.scope_id)] = state


# --- Webhooks ---


def save_webhook(hook: "Webhook") -> None:
    with _lock:
        _webhooks[hook.id] = hook


def get_webhook(webhook_id: str) -> "Webhook | None":
    with _lock:
        return _webhooks.get(webhook_id)


def list_webhooks(organization_id: str, *, limit: int = 100) -> list["Webhook"]:
    with _lock:
        items = [w for w in _webhooks.values() if w.organization_id == organization_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def delete_webhook(webhook_id: str) -> bool:
    with _lock:
        return _webhooks.pop(webhook_id, None) is not None


def save_delivery(delivery: "WebhookDelivery") -> None:
    with _lock:
        _deliveries[delivery.id] = delivery


def get_delivery(delivery_id: str) -> "WebhookDelivery | None":
    with _lock:
        return _deliveries.get(delivery_id)


def list_deliveries(
    organization_id: str,
    *,
    webhook_id: str | None = None,
    status: str | None = None,
    limit: int = 200,
) -> list["WebhookDelivery"]:
    with _lock:
        items = [
            d
            for d in _deliveries.values()
            if d.organization_id == organization_id
            and (webhook_id is None or d.webhook_id == webhook_id)
            and (status is None or d.status == status)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]

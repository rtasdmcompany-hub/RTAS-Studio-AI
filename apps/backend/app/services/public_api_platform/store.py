"""Thread-safe in-memory store for the public API platform."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict, defaultdict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.public_api_platform.models import (
        ApiApplicationRecord,
        ApiTokenRecord,
        ApiUsageLogRecord,
        ApiVersionRecord,
        DeveloperAccountRecord,
        OAuthClientRecord,
        SdkReleaseRecord,
        WebhookSubscriptionRecord,
    )

_lock = threading.RLock()

_developers: OrderedDict[str, "DeveloperAccountRecord"] = OrderedDict()
_developers_by_user: dict[tuple[str, str], str] = {}
_applications: OrderedDict[str, "ApiApplicationRecord"] = OrderedDict()
_oauth_clients: OrderedDict[str, "OAuthClientRecord"] = OrderedDict()
_oauth_by_client_id: dict[str, str] = {}
_tokens: OrderedDict[str, "ApiTokenRecord"] = OrderedDict()
_tokens_by_hash: dict[str, str] = {}
_versions: OrderedDict[str, "ApiVersionRecord"] = OrderedDict()
_usage: OrderedDict[str, "ApiUsageLogRecord"] = OrderedDict()
_sdk_releases: OrderedDict[str, "SdkReleaseRecord"] = OrderedDict()
_webhooks: OrderedDict[str, "WebhookSubscriptionRecord"] = OrderedDict()
_rate_buckets: dict[str, list[float]] = defaultdict(list)

_op_timings: list[float] = []
_op_count = 0
_error_count = 0


def reset_store() -> None:
    global _op_count, _error_count
    with _lock:
        for coll in (
            _developers,
            _developers_by_user,
            _applications,
            _oauth_clients,
            _oauth_by_client_id,
            _tokens,
            _tokens_by_hash,
            _versions,
            _usage,
            _sdk_releases,
            _webhooks,
            _rate_buckets,
        ):
            coll.clear()
        _op_timings.clear()
        _op_count = 0
        _error_count = 0


def record_error() -> None:
    global _error_count
    with _lock:
        _error_count += 1


@contextmanager
def timed_op() -> Iterator[None]:
    global _op_count
    start = time.perf_counter()
    try:
        yield
    except Exception:
        record_error()
        raise
    finally:
        ms = (time.perf_counter() - start) * 1000
        with _lock:
            _op_timings.append(ms)
            if len(_op_timings) > 500:
                del _op_timings[: len(_op_timings) - 500]
            _op_count += 1


def metrics() -> dict[str, Any]:
    with _lock:
        timings = list(_op_timings)
        avg = sum(timings) / len(timings) if timings else 0.0
        return {
            "opCount": _op_count,
            "errorCount": _error_count,
            "avgLatencyMs": round(avg, 3),
            "developers": len(_developers),
            "applications": len(_applications),
            "oauthClients": len(_oauth_clients),
            "apiTokens": len(_tokens),
            "apiVersions": len(_versions),
            "usageLogs": len(_usage),
            "sdkReleases": len(_sdk_releases),
            "webhooks": len(_webhooks),
        }


def save_developer(record: "DeveloperAccountRecord") -> None:
    with _lock:
        _developers[record.id] = record
        _developers_by_user[(record.user_id, record.organization_id)] = record.id


def get_developer(developer_id: str) -> "DeveloperAccountRecord | None":
    with _lock:
        return _developers.get(developer_id)


def get_developer_by_user(
    user_id: str, organization_id: str
) -> "DeveloperAccountRecord | None":
    with _lock:
        did = _developers_by_user.get((user_id, organization_id))
        return _developers.get(did) if did else None


def save_application(record: "ApiApplicationRecord") -> None:
    with _lock:
        _applications[record.id] = record


def get_application(application_id: str) -> "ApiApplicationRecord | None":
    with _lock:
        return _applications.get(application_id)


def list_applications(developer_id: str) -> list["ApiApplicationRecord"]:
    with _lock:
        return [a for a in _applications.values() if a.developer_id == developer_id]


def save_oauth_client(record: "OAuthClientRecord") -> None:
    with _lock:
        _oauth_clients[record.id] = record
        _oauth_by_client_id[record.client_id] = record.id


def get_oauth_client(client_pk: str) -> "OAuthClientRecord | None":
    with _lock:
        return _oauth_clients.get(client_pk)


def get_oauth_by_client_id(client_id: str) -> "OAuthClientRecord | None":
    with _lock:
        pk = _oauth_by_client_id.get(client_id)
        return _oauth_clients.get(pk) if pk else None


def list_oauth_clients(
    *, developer_id: str | None = None, organization_id: str | None = None
) -> list["OAuthClientRecord"]:
    with _lock:
        return [
            c
            for c in _oauth_clients.values()
            if (developer_id is None or c.developer_id == developer_id)
            and (organization_id is None or c.organization_id == organization_id)
            and c.status != "revoked"
        ]


def save_token(record: "ApiTokenRecord") -> None:
    with _lock:
        _tokens[record.id] = record
        _tokens_by_hash[record.token_hash] = record.id


def get_token(token_id: str) -> "ApiTokenRecord | None":
    with _lock:
        return _tokens.get(token_id)


def get_token_by_hash(token_hash: str) -> "ApiTokenRecord | None":
    with _lock:
        tid = _tokens_by_hash.get(token_hash)
        return _tokens.get(tid) if tid else None


def list_tokens(
    *, developer_id: str | None = None, organization_id: str | None = None
) -> list["ApiTokenRecord"]:
    with _lock:
        return [
            t
            for t in _tokens.values()
            if (developer_id is None or t.developer_id == developer_id)
            and (organization_id is None or t.organization_id == organization_id)
            and t.status != "revoked"
        ]


def save_version(record: "ApiVersionRecord") -> None:
    with _lock:
        _versions[record.id] = record


def get_version_by_label(version: str) -> "ApiVersionRecord | None":
    with _lock:
        for v in _versions.values():
            if v.version == version:
                return v
        return None


def list_versions() -> list["ApiVersionRecord"]:
    with _lock:
        items = list(_versions.values())
        items.sort(key=lambda x: x.created_at)
        return items


def save_usage(record: "ApiUsageLogRecord") -> None:
    with _lock:
        _usage[record.id] = record
        if len(_usage) > 100_000:
            _usage.popitem(last=False)


def list_usage(
    *,
    developer_id: str | None = None,
    organization_id: str | None = None,
    limit: int = 100,
) -> list["ApiUsageLogRecord"]:
    with _lock:
        items = [
            u
            for u in _usage.values()
            if (developer_id is None or u.developer_id == developer_id)
            and (organization_id is None or u.organization_id == organization_id)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def save_sdk_release(record: "SdkReleaseRecord") -> None:
    with _lock:
        _sdk_releases[record.id] = record


def list_sdk_releases(
    *, language: str | None = None, limit: int = 100
) -> list["SdkReleaseRecord"]:
    with _lock:
        items = [
            r
            for r in _sdk_releases.values()
            if language is None or r.language == language
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def save_webhook(record: "WebhookSubscriptionRecord") -> None:
    with _lock:
        _webhooks[record.id] = record


def list_webhooks(developer_id: str) -> list["WebhookSubscriptionRecord"]:
    with _lock:
        return [
            w
            for w in _webhooks.values()
            if w.developer_id == developer_id and w.status != "disabled"
        ]


def check_rate_limit(key: str, limit: int, *, window_seconds: float = 60.0) -> bool:
    """Return True if request is allowed under rate limit."""
    now = time.time()
    with _lock:
        bucket = _rate_buckets[key]
        cutoff = now - window_seconds
        _rate_buckets[key] = [t for t in bucket if t >= cutoff]
        if len(_rate_buckets[key]) >= limit:
            return False
        _rate_buckets[key].append(now)
        return True

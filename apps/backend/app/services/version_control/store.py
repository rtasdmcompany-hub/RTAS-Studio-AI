"""Thread-safe in-memory store for version control."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator

from app.services.version_control.version import (
    MAX_APPROVALS,
    MAX_CHANGE_LOGS,
    MAX_REVIEWS,
    MAX_VERSIONS_PER_PROJECT,
)

if TYPE_CHECKING:
    from app.services.version_control.models import (
        ApprovalHistoryEntry,
        ApprovalRequest,
        ChangeLogEntry,
        ProjectVersion,
        Review,
        ReviewComment,
        RollbackRecord,
        VersionSnapshot,
    )

_lock = threading.RLock()
_versions: OrderedDict[str, "ProjectVersion"] = OrderedDict()
_snapshots: OrderedDict[str, "VersionSnapshot"] = OrderedDict()
_approvals: OrderedDict[str, "ApprovalRequest"] = OrderedDict()
_approval_history: OrderedDict[str, "ApprovalHistoryEntry"] = OrderedDict()
_reviews: OrderedDict[str, "Review"] = OrderedDict()
_review_comments: OrderedDict[str, "ReviewComment"] = OrderedDict()
_changelogs: OrderedDict[str, "ChangeLogEntry"] = OrderedDict()
_rollbacks: OrderedDict[str, "RollbackRecord"] = OrderedDict()

_approval_timings: list[float] = []
_api_timings: list[float] = []
_api_count = 0
_error_count = 0
_rollback_events = 0


def reset_store() -> None:
    global _api_count, _error_count, _rollback_events
    with _lock:
        _versions.clear()
        _snapshots.clear()
        _approvals.clear()
        _approval_history.clear()
        _reviews.clear()
        _review_comments.clear()
        _changelogs.clear()
        _rollbacks.clear()
        _approval_timings.clear()
        _api_timings.clear()
        _api_count = 0
        _error_count = 0
        _rollback_events = 0


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


def record_error() -> None:
    global _error_count
    with _lock:
        _error_count += 1


def record_approval_time(seconds: float) -> None:
    with _lock:
        _approval_timings.append(seconds)
        if len(_approval_timings) > 500:
            del _approval_timings[: len(_approval_timings) - 500]


def record_rollback() -> None:
    global _rollback_events
    with _lock:
        _rollback_events += 1


def save_version(v: "ProjectVersion") -> "ProjectVersion":
    with _lock:
        _versions[v.id] = v
        return v


def get_version(vid: str) -> "ProjectVersion | None":
    with _lock:
        return _versions.get(vid)


def list_versions(project_id: str) -> list["ProjectVersion"]:
    with _lock:
        items = [v for v in _versions.values() if v.project_id == project_id]
    items.sort(key=lambda v: v.version_number, reverse=True)
    return items


def count_versions(project_id: str) -> int:
    return len(list_versions(project_id))


def current_version(project_id: str) -> "ProjectVersion | None":
    items = list_versions(project_id)
    for v in items:
        if v.is_current:
            return v
    return items[0] if items else None


def clear_current(project_id: str) -> None:
    with _lock:
        for v in _versions.values():
            if v.project_id == project_id and v.is_current:
                v.is_current = False


def save_snapshot(s: "VersionSnapshot") -> "VersionSnapshot":
    with _lock:
        _snapshots[s.id] = s
        return s


def list_snapshots(version_id: str) -> list["VersionSnapshot"]:
    with _lock:
        items = [s for s in _snapshots.values() if s.version_id == version_id]
    items.sort(key=lambda s: s.created_at, reverse=True)
    return items


def save_approval(a: "ApprovalRequest") -> "ApprovalRequest":
    with _lock:
        _approvals[a.id] = a
        while len(_approvals) > MAX_APPROVALS:
            _approvals.popitem(last=False)
        return a


def get_approval(aid: str) -> "ApprovalRequest | None":
    with _lock:
        return _approvals.get(aid)


def list_approvals(*, project_id: str | None = None, organization_id: str | None = None) -> list["ApprovalRequest"]:
    with _lock:
        items = list(_approvals.values())
    if project_id:
        items = [a for a in items if a.project_id == project_id]
    if organization_id:
        items = [a for a in items if a.organization_id == organization_id]
    items.sort(key=lambda a: a.created_at, reverse=True)
    return items


def save_approval_history(h: "ApprovalHistoryEntry") -> "ApprovalHistoryEntry":
    with _lock:
        _approval_history[h.id] = h
        return h


def list_approval_history(approval_id: str | None = None, *, project_id: str | None = None) -> list["ApprovalHistoryEntry"]:
    with _lock:
        items = list(_approval_history.values())
    if approval_id:
        items = [h for h in items if h.approval_id == approval_id]
    if project_id:
        aids = {a.id for a in list_approvals(project_id=project_id)}
        items = [h for h in items if h.approval_id in aids]
    items.sort(key=lambda h: h.created_at, reverse=True)
    return items


def save_review(r: "Review") -> "Review":
    with _lock:
        _reviews[r.id] = r
        while len(_reviews) > MAX_REVIEWS:
            _reviews.popitem(last=False)
        return r


def get_review(rid: str) -> "Review | None":
    with _lock:
        return _reviews.get(rid)


def list_reviews(*, project_id: str | None = None, organization_id: str | None = None) -> list["Review"]:
    with _lock:
        items = list(_reviews.values())
    if project_id:
        items = [r for r in items if r.project_id == project_id]
    if organization_id:
        items = [r for r in items if r.organization_id == organization_id]
    items.sort(key=lambda r: r.created_at, reverse=True)
    return items


def save_review_comment(c: "ReviewComment") -> "ReviewComment":
    with _lock:
        _review_comments[c.id] = c
        return c


def list_review_comments(review_id: str) -> list["ReviewComment"]:
    with _lock:
        items = [c for c in _review_comments.values() if c.review_id == review_id]
    items.sort(key=lambda c: c.created_at)
    return items


def save_changelog(e: "ChangeLogEntry") -> "ChangeLogEntry":
    with _lock:
        _changelogs[e.id] = e
        while len(_changelogs) > MAX_CHANGE_LOGS:
            _changelogs.popitem(last=False)
        return e


def list_changelog(project_id: str, *, limit: int = 100) -> list["ChangeLogEntry"]:
    with _lock:
        items = [e for e in _changelogs.values() if e.project_id == project_id]
    items.sort(key=lambda e: e.created_at, reverse=True)
    return items[:limit]


def save_rollback(r: "RollbackRecord") -> "RollbackRecord":
    with _lock:
        _rollbacks[r.id] = r
        return r


def list_rollbacks(project_id: str) -> list["RollbackRecord"]:
    with _lock:
        items = [r for r in _rollbacks.values() if r.project_id == project_id]
    items.sort(key=lambda r: r.created_at, reverse=True)
    return items


def metrics() -> dict:
    with _lock:
        avg_api = sum(_api_timings) / len(_api_timings) if _api_timings else 0.0
        avg_approval = (
            sum(_approval_timings) / len(_approval_timings) if _approval_timings else 0.0
        )
        return {
            "versionCount": len(_versions),
            "reviewCount": len(_reviews),
            "approvalCount": len(_approvals),
            "approvalTimeSec": round(avg_approval, 3),
            "rollbackEvents": _rollback_events,
            "changeHistory": len(_changelogs),
            "snapshotCount": len(_snapshots),
            "errors": _error_count,
            "apiCalls": _api_count,
            "avgLatencyMs": round(avg_api, 2),
            "maxVersionsPerProject": MAX_VERSIONS_PER_PROJECT,
        }

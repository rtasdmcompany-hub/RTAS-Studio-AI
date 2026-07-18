"""Thread-safe in-memory store for enterprise communications."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator

from app.services.enterprise_comms.version import (
    MAX_ACTIVITY,
    MAX_ANNOUNCEMENTS,
    MAX_COMMENTS,
    MAX_NOTIFICATIONS,
    MAX_USER_LOGS,
)

if TYPE_CHECKING:
    from app.services.enterprise_comms.models import (
        ActivityEvent,
        Announcement,
        Comment,
        CommentReply,
        Mention,
        Notification,
        NotificationPreference,
        UserActivityLog,
    )

_lock = threading.RLock()
_notifications: OrderedDict[str, "Notification"] = OrderedDict()
_preferences: OrderedDict[str, "NotificationPreference"] = OrderedDict()
_comments: OrderedDict[str, "Comment"] = OrderedDict()
_replies: OrderedDict[str, "CommentReply"] = OrderedDict()
_mentions: OrderedDict[str, "Mention"] = OrderedDict()
_activity: OrderedDict[str, "ActivityEvent"] = OrderedDict()
_announcements: OrderedDict[str, "Announcement"] = OrderedDict()
_user_logs: OrderedDict[str, "UserActivityLog"] = OrderedDict()
_pref_key: dict[tuple[str, str | None], str] = {}

_notifications_sent = 0
_notifications_read = 0
_active_users: set[str] = set()
_api_timings: list[float] = []
_api_count = 0
_error_count = 0


def reset_store() -> None:
    global _notifications_sent, _notifications_read, _api_count, _error_count
    with _lock:
        _notifications.clear()
        _preferences.clear()
        _comments.clear()
        _replies.clear()
        _mentions.clear()
        _activity.clear()
        _announcements.clear()
        _user_logs.clear()
        _pref_key.clear()
        _active_users.clear()
        _api_timings.clear()
        _notifications_sent = 0
        _notifications_read = 0
        _api_count = 0
        _error_count = 0


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


def touch_user(user_id: str) -> None:
    with _lock:
        _active_users.add(user_id)


def save_notification(n: "Notification") -> "Notification":
    global _notifications_sent
    with _lock:
        _notifications[n.id] = n
        _notifications_sent += 1
        while len(_notifications) > MAX_NOTIFICATIONS:
            _notifications.popitem(last=False)
        return n


def get_notification(nid: str) -> "Notification | None":
    with _lock:
        return _notifications.get(nid)


def list_notifications(
    *,
    recipient_id: str,
    organization_id: str | None = None,
    unread_only: bool = False,
    limit: int = 50,
) -> list["Notification"]:
    with _lock:
        items = list(_notifications.values())
    items = [n for n in items if n.recipient_id == recipient_id]
    if organization_id:
        items = [n for n in items if n.organization_id == organization_id]
    if unread_only:
        items = [n for n in items if not n.is_read]
    items.sort(key=lambda n: n.created_at, reverse=True)
    return items[:limit]


def mark_read(ids: list[str], *, recipient_id: str) -> int:
    global _notifications_read
    count = 0
    with _lock:
        for nid in ids:
            n = _notifications.get(nid)
            if n and n.recipient_id == recipient_id and not n.is_read:
                from datetime import datetime, timezone

                n.is_read = True
                n.read_at = datetime.now(timezone.utc)
                _notifications_read += 1
                count += 1
    return count


def mark_all_read(*, recipient_id: str, organization_id: str | None = None) -> int:
    ids = [
        n.id
        for n in list_notifications(
            recipient_id=recipient_id,
            organization_id=organization_id,
            unread_only=True,
            limit=10000,
        )
    ]
    return mark_read(ids, recipient_id=recipient_id)


def save_preference(p: "NotificationPreference") -> "NotificationPreference":
    with _lock:
        _preferences[p.id] = p
        _pref_key[(p.user_id, p.organization_id)] = p.id
        return p


def get_preference(user_id: str, organization_id: str | None = None) -> "NotificationPreference | None":
    with _lock:
        pid = _pref_key.get((user_id, organization_id))
        return _preferences.get(pid) if pid else None


def save_comment(c: "Comment") -> "Comment":
    with _lock:
        _comments[c.id] = c
        while len(_comments) > MAX_COMMENTS:
            _comments.popitem(last=False)
        return c


def get_comment(cid: str) -> "Comment | None":
    with _lock:
        return _comments.get(cid)


def list_comments(
    *,
    resource_id: str,
    resource_type: str | None = None,
    organization_id: str | None = None,
    include_deleted: bool = False,
) -> list["Comment"]:
    with _lock:
        items = list(_comments.values())
    items = [c for c in items if c.resource_id == resource_id]
    if resource_type:
        items = [c for c in items if c.resource_type == resource_type]
    if organization_id:
        items = [c for c in items if c.organization_id == organization_id]
    if not include_deleted:
        items = [c for c in items if c.deleted_at is None]
    items.sort(key=lambda c: (not c.is_pinned, c.created_at))
    return items


def save_reply(r: "CommentReply") -> "CommentReply":
    with _lock:
        _replies[r.id] = r
        return r


def list_replies(comment_id: str, *, include_deleted: bool = False) -> list["CommentReply"]:
    with _lock:
        items = [r for r in _replies.values() if r.comment_id == comment_id]
    if not include_deleted:
        items = [r for r in items if r.deleted_at is None]
    items.sort(key=lambda r: r.created_at)
    return items


def get_reply(rid: str) -> "CommentReply | None":
    with _lock:
        return _replies.get(rid)


def save_mention(m: "Mention") -> "Mention":
    with _lock:
        _mentions[m.id] = m
        return m


def list_mentions(*, organization_id: str | None = None, target_user_id: str | None = None) -> list["Mention"]:
    with _lock:
        items = list(_mentions.values())
    if organization_id:
        items = [m for m in items if m.organization_id == organization_id]
    if target_user_id:
        items = [m for m in items if m.target_user_id == target_user_id]
    items.sort(key=lambda m: m.created_at, reverse=True)
    return items


def save_activity(e: "ActivityEvent") -> "ActivityEvent":
    with _lock:
        _activity[e.id] = e
        while len(_activity) > MAX_ACTIVITY:
            _activity.popitem(last=False)
        return e


def list_activity(
    *,
    organization_id: str,
    workspace_id: str | None = None,
    category: str | None = None,
    limit: int = 50,
) -> list["ActivityEvent"]:
    with _lock:
        items = [e for e in _activity.values() if e.organization_id == organization_id]
    if workspace_id:
        items = [e for e in items if e.workspace_id == workspace_id]
    if category:
        items = [e for e in items if e.category == category]
    items.sort(key=lambda e: e.created_at, reverse=True)
    return items[:limit]


def save_announcement(a: "Announcement") -> "Announcement":
    with _lock:
        _announcements[a.id] = a
        while len(_announcements) > MAX_ANNOUNCEMENTS:
            _announcements.popitem(last=False)
        return a


def list_announcements(*, organization_id: str, workspace_id: str | None = None) -> list["Announcement"]:
    with _lock:
        items = [a for a in _announcements.values() if a.organization_id == organization_id]
    if workspace_id:
        items = [a for a in items if a.workspace_id == workspace_id or a.scope == "organization"]
    items.sort(key=lambda a: (not a.is_pinned, a.published_at), reverse=True)
    return items


def save_user_log(log: "UserActivityLog") -> "UserActivityLog":
    with _lock:
        _user_logs[log.id] = log
        _active_users.add(log.user_id)
        while len(_user_logs) > MAX_USER_LOGS:
            _user_logs.popitem(last=False)
        return log


def metrics() -> dict:
    with _lock:
        avg = sum(_api_timings) / len(_api_timings) if _api_timings else 0.0
        return {
            "notificationsSent": _notifications_sent,
            "notificationsRead": _notifications_read,
            "activeUsers": len(_active_users),
            "commentCount": sum(1 for c in _comments.values() if c.deleted_at is None),
            "mentionCount": len(_mentions),
            "activityEvents": len(_activity),
            "announcementCount": len(_announcements),
            "errors": _error_count,
            "apiCalls": _api_count,
            "avgLatencyMs": round(avg, 2),
        }

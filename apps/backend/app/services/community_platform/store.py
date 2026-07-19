"""Thread-safe in-memory store for the community platform."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.community_platform.models import (
        ActivityEvent,
        Comment,
        Engagement,
        FollowEdge,
        Notification,
        RatingRecord,
        Review,
        UserProfile,
    )

_lock = threading.RLock()

_profiles: OrderedDict[str, "UserProfile"] = OrderedDict()
_profile_by_user: dict[tuple[str, str], str] = {}
_profile_by_handle: dict[tuple[str, str], str] = {}
_follows: OrderedDict[str, "FollowEdge"] = OrderedDict()
_follow_keys: dict[tuple[str, str, str], str] = {}
_reviews: OrderedDict[str, "Review"] = OrderedDict()
_ratings: OrderedDict[str, "RatingRecord"] = OrderedDict()
_comments: OrderedDict[str, "Comment"] = OrderedDict()
_engagements: OrderedDict[str, "Engagement"] = OrderedDict()
_engagement_keys: dict[tuple[str, str, str], str] = {}  # (asset, user, kind)
_notifications: OrderedDict[str, "Notification"] = OrderedDict()
_activity: OrderedDict[str, "ActivityEvent"] = OrderedDict()
_featured: dict[str, dict[str, list[str]]] = {}  # org -> {"creators": [], "assets": []}

_op_timings: list[float] = []
_op_count = 0
_error_count = 0


def reset_store() -> None:
    global _op_count, _error_count
    with _lock:
        for coll in (
            _profiles, _profile_by_user, _profile_by_handle, _follows, _follow_keys,
            _reviews, _ratings, _comments, _engagements, _engagement_keys,
            _notifications, _activity, _featured,
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
            "profiles": len(_profiles),
            "follows": len(_follows),
            "reviews": len(_reviews),
            "ratings": len(_ratings),
            "comments": len(_comments),
            "engagements": len(_engagements),
            "notifications": len(_notifications),
            "activityEvents": len(_activity),
        }


# --- Profiles ---


def save_profile(profile: "UserProfile") -> None:
    with _lock:
        _profiles[profile.id] = profile
        _profile_by_user[(profile.organization_id, profile.user_id)] = profile.id
        _profile_by_handle[(profile.organization_id, profile.handle.lower())] = profile.id


def get_profile(profile_id: str) -> "UserProfile | None":
    with _lock:
        return _profiles.get(profile_id)


def get_profile_by_user(organization_id: str, user_id: str) -> "UserProfile | None":
    with _lock:
        pid = _profile_by_user.get((organization_id, user_id))
        return _profiles.get(pid) if pid else None


def get_profile_by_handle(organization_id: str, handle: str) -> "UserProfile | None":
    with _lock:
        pid = _profile_by_handle.get((organization_id, handle.lower()))
        return _profiles.get(pid) if pid else None


def list_profiles(organization_id: str) -> list["UserProfile"]:
    with _lock:
        return [p for p in _profiles.values() if p.organization_id == organization_id]


# --- Follows ---


def save_follow(edge: "FollowEdge") -> None:
    with _lock:
        _follows[edge.id] = edge
        _follow_keys[
            (edge.organization_id, edge.follower_user_id, edge.target_user_id)
        ] = edge.id


def remove_follow(organization_id: str, follower: str, target: str) -> bool:
    with _lock:
        fid = _follow_keys.pop((organization_id, follower, target), None)
        if fid is None:
            return False
        _follows.pop(fid, None)
        return True


def is_following(organization_id: str, follower: str, target: str) -> bool:
    with _lock:
        return (organization_id, follower, target) in _follow_keys


def list_followers(organization_id: str, target: str) -> list["FollowEdge"]:
    with _lock:
        return [
            f
            for f in _follows.values()
            if f.organization_id == organization_id and f.target_user_id == target
        ]


def list_following(organization_id: str, follower: str) -> list["FollowEdge"]:
    with _lock:
        return [
            f
            for f in _follows.values()
            if f.organization_id == organization_id
            and f.follower_user_id == follower
        ]


def list_follows(organization_id: str) -> list["FollowEdge"]:
    with _lock:
        return [f for f in _follows.values() if f.organization_id == organization_id]


# --- Reviews & ratings ---


def save_review(review: "Review") -> None:
    with _lock:
        _reviews[review.id] = review


def get_review(review_id: str) -> "Review | None":
    with _lock:
        return _reviews.get(review_id)


def list_reviews(
    *,
    organization_id: str | None = None,
    asset_id: str | None = None,
    author: str | None = None,
    include_hidden: bool = False,
) -> list["Review"]:
    with _lock:
        return [
            r
            for r in _reviews.values()
            if (organization_id is None or r.organization_id == organization_id)
            and (asset_id is None or r.asset_id == asset_id)
            and (author is None or r.author_user_id == author)
            and (include_hidden or r.status == "visible")
        ]


def save_rating(rating: "RatingRecord") -> None:
    with _lock:
        _ratings[rating.id] = rating


def list_ratings(
    *, organization_id: str | None = None, asset_id: str | None = None,
    user_id: str | None = None,
) -> list["RatingRecord"]:
    with _lock:
        return [
            r
            for r in _ratings.values()
            if (organization_id is None or r.organization_id == organization_id)
            and (asset_id is None or r.asset_id == asset_id)
            and (user_id is None or r.user_id == user_id)
        ]


# --- Comments ---


def save_comment(comment: "Comment") -> None:
    with _lock:
        _comments[comment.id] = comment


def get_comment(comment_id: str) -> "Comment | None":
    with _lock:
        return _comments.get(comment_id)


def list_comments(
    *,
    organization_id: str | None = None,
    subject_id: str | None = None,
    author: str | None = None,
    parent_id: str | None = None,
    include_hidden: bool = False,
) -> list["Comment"]:
    with _lock:
        return [
            c
            for c in _comments.values()
            if (organization_id is None or c.organization_id == organization_id)
            and (subject_id is None or c.subject_id == subject_id)
            and (author is None or c.author_user_id == author)
            and (parent_id is None or c.parent_id == parent_id)
            and (include_hidden or c.status != "removed")
        ]


# --- Engagements ---


def save_engagement(engagement: "Engagement") -> None:
    with _lock:
        _engagements[engagement.id] = engagement
        _engagement_keys[
            (engagement.asset_id, engagement.user_id, engagement.kind)
        ] = engagement.id


def remove_engagement(asset_id: str, user_id: str, kind: str) -> bool:
    with _lock:
        eid = _engagement_keys.pop((asset_id, user_id, kind), None)
        if eid is None:
            return False
        _engagements.pop(eid, None)
        return True


def has_engagement(asset_id: str, user_id: str, kind: str) -> bool:
    with _lock:
        return (asset_id, user_id, kind) in _engagement_keys


def list_engagements(
    *,
    organization_id: str | None = None,
    asset_id: str | None = None,
    user_id: str | None = None,
    kind: str | None = None,
) -> list["Engagement"]:
    with _lock:
        return [
            e
            for e in _engagements.values()
            if (organization_id is None or e.organization_id == organization_id)
            and (asset_id is None or e.asset_id == asset_id)
            and (user_id is None or e.user_id == user_id)
            and (kind is None or e.kind == kind)
        ]


# --- Notifications ---


def save_notification(notification: "Notification") -> None:
    with _lock:
        _notifications[notification.id] = notification
        if len(_notifications) > 100_000:
            _notifications.popitem(last=False)


def get_notification(notification_id: str) -> "Notification | None":
    with _lock:
        return _notifications.get(notification_id)


def list_notifications(
    organization_id: str, recipient: str, *, unread_only: bool = False
) -> list["Notification"]:
    with _lock:
        items = [
            n
            for n in _notifications.values()
            if n.organization_id == organization_id
            and n.recipient_user_id == recipient
            and (not unread_only or not n.read)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items


# --- Activity ---


def save_activity(event: "ActivityEvent") -> None:
    with _lock:
        _activity[event.id] = event
        if len(_activity) > 100_000:
            _activity.popitem(last=False)


def list_activity(
    *, organization_id: str, actor: str | None = None, since: datetime | None = None,
) -> list["ActivityEvent"]:
    with _lock:
        items = [
            a
            for a in _activity.values()
            if a.organization_id == organization_id
            and (actor is None or a.actor_user_id == actor)
            and (since is None or a.created_at >= since)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items


# --- Featured ---


def set_featured(organization_id: str, creators: list[str], assets: list[str]) -> None:
    with _lock:
        _featured[organization_id] = {"creators": creators, "assets": assets}


def get_featured(organization_id: str) -> dict[str, list[str]]:
    with _lock:
        data = _featured.get(organization_id) or {}
        return {
            "creators": list(data.get("creators") or []),
            "assets": list(data.get("assets") or []),
        }

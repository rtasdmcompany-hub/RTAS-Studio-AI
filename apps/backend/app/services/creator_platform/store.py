"""Thread-safe in-memory store for the creator platform & publisher ecosystem."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.creator_platform.models import (
        CreatorAccount,
        CreatorBadge,
        CreatorFollower,
        CreatorProfile,
        EngagementEvent,
        PublisherAsset,
    )

_lock = threading.RLock()

_creators: OrderedDict[str, "CreatorAccount"] = OrderedDict()
_creator_by_user: dict[tuple[str, str], str] = {}
_profiles: dict[str, "CreatorProfile"] = {}  # keyed by creator_id
_badges: OrderedDict[str, "CreatorBadge"] = OrderedDict()
_followers: OrderedDict[str, "CreatorFollower"] = OrderedDict()
_follower_keys: dict[tuple[str, str], str] = {}
_assets: OrderedDict[str, "PublisherAsset"] = OrderedDict()
_events: OrderedDict[str, "EngagementEvent"] = OrderedDict()

_op_timings: list[float] = []
_op_count = 0
_error_count = 0


def reset_store() -> None:
    global _op_count, _error_count
    with _lock:
        _creators.clear()
        _creator_by_user.clear()
        _profiles.clear()
        _badges.clear()
        _followers.clear()
        _follower_keys.clear()
        _assets.clear()
        _events.clear()
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
            "creators": len(_creators),
            "profiles": len(_profiles),
            "badges": len(_badges),
            "followers": len(_followers),
            "assets": len(_assets),
            "engagementEvents": len(_events),
        }


# --- Creators & profiles ---


def save_creator(creator: "CreatorAccount") -> None:
    with _lock:
        _creators[creator.id] = creator
        _creator_by_user[(creator.organization_id, creator.user_id)] = creator.id


def get_creator(creator_id: str) -> "CreatorAccount | None":
    with _lock:
        return _creators.get(creator_id)


def get_creator_by_user(organization_id: str, user_id: str) -> "CreatorAccount | None":
    with _lock:
        cid = _creator_by_user.get((organization_id, user_id))
        return _creators.get(cid) if cid else None


def list_creators(*, organization_id: str | None = None) -> list["CreatorAccount"]:
    with _lock:
        items = [
            c
            for c in _creators.values()
            if organization_id is None or c.organization_id == organization_id
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items


def save_profile(profile: "CreatorProfile") -> None:
    with _lock:
        _profiles[profile.creator_id] = profile


def get_profile(creator_id: str) -> "CreatorProfile | None":
    with _lock:
        return _profiles.get(creator_id)


# --- Badges ---


def save_badge(badge: "CreatorBadge") -> None:
    with _lock:
        _badges[badge.id] = badge


def list_badges(creator_id: str) -> list["CreatorBadge"]:
    with _lock:
        items = [b for b in _badges.values() if b.creator_id == creator_id]
        items.sort(key=lambda x: x.awarded_at)
        return items


def has_badge(creator_id: str, badge_key: str) -> bool:
    with _lock:
        return any(
            b.creator_id == creator_id and b.badge_key == badge_key
            for b in _badges.values()
        )


# --- Followers ---


def save_follower(follower: "CreatorFollower") -> None:
    with _lock:
        _followers[follower.id] = follower
        _follower_keys[(follower.creator_id, follower.follower_user_id)] = follower.id


def remove_follower(creator_id: str, follower_user_id: str) -> bool:
    with _lock:
        fid = _follower_keys.pop((creator_id, follower_user_id), None)
        if fid is None:
            return False
        _followers.pop(fid, None)
        return True


def is_following(creator_id: str, follower_user_id: str) -> bool:
    with _lock:
        return (creator_id, follower_user_id) in _follower_keys


def count_followers(creator_id: str) -> int:
    with _lock:
        return sum(1 for f in _followers.values() if f.creator_id == creator_id)


# --- Publisher assets ---


def save_asset(asset: "PublisherAsset") -> None:
    with _lock:
        _assets[asset.id] = asset


def get_asset(asset_id: str) -> "PublisherAsset | None":
    with _lock:
        return _assets.get(asset_id)


def list_assets(
    *,
    organization_id: str | None = None,
    creator_id: str | None = None,
    status: str | None = None,
    include_deleted: bool = False,
    limit: int = 10_000,
) -> list["PublisherAsset"]:
    with _lock:
        items = [
            a
            for a in _assets.values()
            if (organization_id is None or a.organization_id == organization_id)
            and (creator_id is None or a.creator_id == creator_id)
            and (status is None or a.status == status)
            and (include_deleted or a.status != "deleted")
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def list_due_scheduled(now) -> list["PublisherAsset"]:
    with _lock:
        return [
            a
            for a in _assets.values()
            if a.status == "scheduled"
            and a.publish_at is not None
            and a.publish_at <= now
        ]


# --- Engagement events ---


def save_event(event: "EngagementEvent") -> None:
    with _lock:
        _events[event.id] = event
        if len(_events) > 100_000:
            _events.popitem(last=False)


def list_events(
    *, creator_id: str | None = None, event_type: str | None = None
) -> list["EngagementEvent"]:
    with _lock:
        return [
            e
            for e in _events.values()
            if (creator_id is None or e.creator_id == creator_id)
            and (event_type is None or e.event_type == event_type)
        ]

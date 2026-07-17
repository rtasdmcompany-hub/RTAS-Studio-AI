"""Scene cache — fingerprinting and LRU-style in-memory cache."""

from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict
from typing import Any

from app.services.scene_render.models import SceneCacheEntry

_lock = threading.Lock()
_CACHE: OrderedDict[str, dict[str, Any]] = OrderedDict()
_MAX_ENTRIES = 256
_MAX_MB = 512.0


def fingerprint_scene(
    scene: dict[str, Any],
    *,
    lighting_key: str,
    quality: str,
    physics_effects: list[str] | None = None,
) -> str:
    payload = "|".join(
        [
            str(scene.get("index", scene.get("scene_index", ""))),
            str(scene.get("title") or ""),
            str(scene.get("description") or "")[:200],
            str(scene.get("environment") or ""),
            lighting_key,
            quality,
            ",".join(physics_effects or []),
        ]
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def estimate_size_mb(
    *,
    quality: str,
    has_particles: bool,
    duration_seconds: float,
) -> float:
    base = {"draft": 24.0, "preview": 48.0, "production": 96.0, "cinema": 160.0}.get(
        quality, 64.0
    )
    if has_particles:
        base *= 1.25
    base += min(40.0, float(duration_seconds or 0) * 2.0)
    return round(base, 2)


def build_cache_entry(
    scene: dict[str, Any],
    *,
    scene_index: int,
    lighting_key: str,
    quality: str,
    physics_effects: list[str] | None = None,
    assets: list[str] | None = None,
    duration_seconds: float = 4.0,
) -> SceneCacheEntry:
    fp = fingerprint_scene(
        scene,
        lighting_key=lighting_key,
        quality=quality,
        physics_effects=physics_effects,
    )
    cache_key = f"scache_{scene_index}_{fp}"
    size = estimate_size_mb(
        quality=quality,
        has_particles=bool(physics_effects),
        duration_seconds=duration_seconds,
    )

    hits = 0
    stale = False
    with _lock:
        existing = _CACHE.get(cache_key)
        if existing:
            existing["hits"] = int(existing.get("hits", 0)) + 1
            hits = existing["hits"]
            _CACHE.move_to_end(cache_key)
        else:
            _CACHE[cache_key] = {
                "fingerprint": fp,
                "hits": 0,
                "size_estimate_mb": size,
                "scene_index": scene_index,
            }
            hits = 0
            _evict_locked()

    return SceneCacheEntry(
        cache_key=cache_key,
        scene_index=scene_index,
        fingerprint=fp,
        hits=hits,
        size_estimate_mb=size,
        assets=list(assets or [])[:16],
        stale=stale,
    )


def _evict_locked() -> None:
    total = sum(float(v.get("size_estimate_mb") or 0) for v in _CACHE.values())
    while len(_CACHE) > _MAX_ENTRIES or total > _MAX_MB:
        if not _CACHE:
            break
        _, removed = _CACHE.popitem(last=False)
        total -= float(removed.get("size_estimate_mb") or 0)


def cache_stats() -> dict[str, Any]:
    with _lock:
        total = sum(float(v.get("size_estimate_mb") or 0) for v in _CACHE.values())
        return {
            "entries": len(_CACHE),
            "size_mb": round(total, 2),
            "max_entries": _MAX_ENTRIES,
            "max_mb": _MAX_MB,
        }


def clear_cache() -> None:
    with _lock:
        _CACHE.clear()

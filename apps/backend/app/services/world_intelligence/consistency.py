"""World consistency + environment memory."""

from __future__ import annotations

import hashlib
import threading
from collections import defaultdict
from typing import Any

from app.services.world_intelligence.models import (
    ConsistencyReport,
    EnvironmentBlueprint,
    WORLD_CONSISTENCY_TRAITS,
)
from app.services.world_intelligence.version import WORLD_CONSISTENCY_THRESHOLD

_lock = threading.Lock()
_memory: dict[str, list[dict[str, Any]]] = defaultdict(list)
_MAX = 50


def memory_key(world_id: str | None) -> str:
    wid = (world_id or "anon").strip() or "anon"
    return f"wmem_{hashlib.sha1(wid.encode()).hexdigest()[:12]}"


def remember_world(world_id: str, blueprint: EnvironmentBlueprint, job_id: str) -> None:
    key = memory_key(world_id)
    entry = {
        "fingerprint": blueprint.fingerprint(),
        "environment": blueprint.environment_id,
        "weather": blueprint.weather.weather_id,
        "time_of_day": blueprint.time_of_day,
        "lighting": blueprint.lighting.lighting_id,
        "location_id": blueprint.location_id,
        "job_id": job_id,
    }
    with _lock:
        bucket = _memory[key]
        bucket.append(entry)
        while len(bucket) > _MAX:
            bucket.pop(0)


def last_blueprint_snapshot(world_id: str) -> dict[str, Any] | None:
    key = memory_key(world_id)
    with _lock:
        bucket = _memory.get(key) or []
        return dict(bucket[-1]) if bucket else None


def clear_memory() -> None:
    with _lock:
        _memory.clear()


def verify_consistency(
    world_id: str,
    locked: EnvironmentBlueprint,
    candidate: EnvironmentBlueprint | None = None,
) -> ConsistencyReport:
    cand = candidate or locked
    flags: list[str] = []
    checks = [
        ("location", locked.location_id, cand.location_id),
        ("weather", locked.weather.weather_id, cand.weather.weather_id),
        ("time_of_day", locked.time_of_day, cand.time_of_day),
        ("lighting", locked.lighting.lighting_id, cand.lighting.lighting_id),
        ("sky", locked.sky, cand.sky),
    ]
    for name, a, b in checks:
        if a != b:
            flags.append(f"{name}_drift:{a}->{b}")

    # Asset continuity
    for asset_key in ("buildings", "roads", "trees"):
        if locked.assets.get(asset_key) != cand.assets.get(asset_key):
            flags.append(f"{asset_key}_asset_drift")

    score = max(0.0, 100.0 - len(flags) * 12.0)
    if locked.fingerprint() == cand.fingerprint():
        score = max(score, 99.0)
    no_breaks = len(flags) == 0
    return ConsistencyReport(
        world_id=world_id,
        consistent=score >= WORLD_CONSISTENCY_THRESHOLD and no_breaks,
        score=round(score, 2),
        preserved_traits=list(WORLD_CONSISTENCY_TRAITS),
        drift_flags=flags,
        no_continuity_breaks=no_breaks,
    )

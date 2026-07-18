"""Director memory — retain prior production decisions per project."""

from __future__ import annotations

import hashlib
import threading
from collections import defaultdict
from typing import Any

_lock = threading.Lock()
_memory: dict[str, list[dict[str, Any]]] = defaultdict(list)
_MAX = 50


def memory_key(project_id: str | None) -> str:
    pid = (project_id or "anon").strip() or "anon"
    return f"dmem_{hashlib.sha1(pid.encode()).hexdigest()[:12]}"


def remember_plan(project_id: str, plan: dict[str, Any], job_id: str) -> None:
    key = memory_key(project_id)
    entry = {
        "plan_id": plan.get("plan_id"),
        "format_type": plan.get("format_type"),
        "scene_count": len(plan.get("scenes") or []),
        "shot_count": plan.get("shot_count"),
        "runtime_sec": plan.get("total_runtime_sec"),
        "story_structure": list(plan.get("story_structure") or []),
        "job_id": job_id,
    }
    with _lock:
        bucket = _memory[key]
        bucket.append(entry)
        while len(bucket) > _MAX:
            bucket.pop(0)


def last_plan(project_id: str) -> dict[str, Any] | None:
    key = memory_key(project_id)
    with _lock:
        bucket = _memory.get(key) or []
        return dict(bucket[-1]) if bucket else None


def history_for(project_id: str) -> list[dict[str, Any]]:
    key = memory_key(project_id)
    with _lock:
        return [dict(x) for x in (_memory.get(key) or [])]


def clear() -> None:
    with _lock:
        _memory.clear()

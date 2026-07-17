"""Performance Memory — remember character emotion history across jobs."""

from __future__ import annotations

import hashlib
import threading
from collections import defaultdict
from typing import Any

_lock = threading.Lock()
_memory: dict[str, list[dict[str, Any]]] = defaultdict(list)
_MAX_PER_CHARACTER = 50


def memory_key(character_id: str | None) -> str:
    cid = (character_id or "anonymous").strip() or "anonymous"
    return f"emem_{hashlib.sha1(cid.encode()).hexdigest()[:12]}"


def remember(
    character_id: str | None,
    *,
    emotion: str,
    intensity: float,
    expression_score: float,
    job_id: str,
) -> dict[str, Any]:
    key = memory_key(character_id)
    entry = {
        "emotion": emotion,
        "intensity": intensity,
        "expression_score": expression_score,
        "job_id": job_id,
    }
    with _lock:
        bucket = _memory[key]
        bucket.append(entry)
        while len(bucket) > _MAX_PER_CHARACTER:
            bucket.pop(0)
        return {"memory_key": key, "count": len(bucket), "latest": entry}


def last_emotion(character_id: str | None) -> str | None:
    key = memory_key(character_id)
    with _lock:
        bucket = _memory.get(key) or []
        if not bucket:
            return None
        return str(bucket[-1].get("emotion"))


def history_for(character_id: str | None, limit: int = 20) -> list[dict[str, Any]]:
    key = memory_key(character_id)
    with _lock:
        bucket = list(_memory.get(key) or [])
    return list(reversed(bucket[-max(1, min(50, limit)) :]))


def clear() -> None:
    with _lock:
        _memory.clear()

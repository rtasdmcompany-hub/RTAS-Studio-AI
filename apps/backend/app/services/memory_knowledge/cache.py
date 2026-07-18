"""Simple TTL cache for retrieval / context loads."""

from __future__ import annotations

import threading
import time
from typing import Any

from app.services.memory_knowledge.version import CACHE_TTL_SEC

_lock = threading.Lock()
_cache: dict[str, tuple[float, Any]] = {}
_hits = 0
_misses = 0


def get(key: str) -> Any | None:
    global _hits, _misses
    now = time.time()
    with _lock:
        item = _cache.get(key)
        if not item:
            _misses += 1
            return None
        exp, value = item
        if exp < now:
            _cache.pop(key, None)
            _misses += 1
            return None
        _hits += 1
        return value


def set(key: str, value: Any, *, ttl: float | None = None) -> None:
    with _lock:
        _cache[key] = (time.time() + float(ttl or CACHE_TTL_SEC), value)


def hit_rate() -> float:
    with _lock:
        total = _hits + _misses
        return (_hits / total * 100.0) if total else 100.0


def stats() -> dict[str, float | int]:
    with _lock:
        total = _hits + _misses
        return {
            "hits": _hits,
            "misses": _misses,
            "entries": len(_cache),
            "hit_rate": round((_hits / total * 100.0) if total else 100.0, 2),
        }


def clear() -> None:
    global _hits, _misses
    with _lock:
        _cache.clear()
        _hits = 0
        _misses = 0

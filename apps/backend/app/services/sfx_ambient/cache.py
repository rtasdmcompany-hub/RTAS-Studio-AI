"""Lightweight cache for layers and environment lookups."""

from __future__ import annotations

import threading
import time
from typing import Any

_lock = threading.Lock()
_CACHE: dict[str, tuple[float, Any]] = {}
_TTL = 300.0
_MAX = 500


def cache_get(key: str) -> Any | None:
    with _lock:
        item = _CACHE.get(key)
        if not item:
            return None
        expires, value = item
        if time.time() > expires:
            _CACHE.pop(key, None)
            return None
        return value


def cache_set(key: str, value: Any, *, ttl: float = _TTL) -> None:
    with _lock:
        _CACHE[key] = (time.time() + ttl, value)
        while len(_CACHE) > _MAX:
            oldest = min(_CACHE.items(), key=lambda kv: kv[1][0])[0]
            _CACHE.pop(oldest, None)


def cache_invalidate(prefix: str = "") -> None:
    with _lock:
        if not prefix:
            _CACHE.clear()
            return
        for key in list(_CACHE.keys()):
            if key.startswith(prefix):
                _CACHE.pop(key, None)

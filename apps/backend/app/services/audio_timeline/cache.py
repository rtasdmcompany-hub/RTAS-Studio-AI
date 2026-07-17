"""Lightweight timeline cache."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any

_lock = threading.Lock()
_cache: OrderedDict[str, tuple[float, dict[str, Any]]] = OrderedDict()
_TTL = 600.0
_MAX = 500


def cache_get(key: str) -> dict[str, Any] | None:
    with _lock:
        item = _cache.get(key)
        if not item:
            return None
        ts, payload = item
        if time.time() - ts > _TTL:
            _cache.pop(key, None)
            return None
        _cache.move_to_end(key)
        return dict(payload)


def cache_set(key: str, payload: dict[str, Any]) -> None:
    with _lock:
        _cache[key] = (time.time(), dict(payload))
        _cache.move_to_end(key)
        while len(_cache) > _MAX:
            _cache.popitem(last=False)


def cache_clear() -> None:
    with _lock:
        _cache.clear()


def cache_size() -> int:
    with _lock:
        return len(_cache)

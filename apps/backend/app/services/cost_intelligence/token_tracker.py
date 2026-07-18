"""Token Usage Tracker."""

from __future__ import annotations

import threading

_lock = threading.Lock()
_by_provider: dict[str, int] = {}
_total: int = 0


def record(provider: str, tokens: int) -> int:
    global _total
    n = max(0, int(tokens))
    key = (provider or "unknown").lower()
    with _lock:
        _by_provider[key] = _by_provider.get(key, 0) + n
        _total += n
        return _by_provider[key]


def get(provider: str | None = None) -> dict[str, int] | int:
    with _lock:
        if provider is None:
            return dict(_by_provider)
        return _by_provider.get(provider.lower(), 0)


def total() -> int:
    with _lock:
        return _total


def clear() -> None:
    global _total
    with _lock:
        _by_provider.clear()
        _total = 0

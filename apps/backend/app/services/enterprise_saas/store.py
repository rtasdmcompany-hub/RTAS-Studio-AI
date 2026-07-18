"""In-memory results store for Phase 7 final validation."""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from typing import Any, Iterator

_lock = threading.RLock()
_last_validation: dict[str, Any] = {}
_last_stress: dict[str, Any] = {}
_last_scores: dict[str, Any] = {}
_api_timings: list[float] = []
_api_count = 0
_error_count = 0


def reset_store() -> None:
    global _api_count, _error_count
    with _lock:
        _last_validation.clear()
        _last_stress.clear()
        _last_scores.clear()
        _api_timings.clear()
        _api_count = 0
        _error_count = 0


@contextmanager
def timed_op() -> Iterator[None]:
    global _api_count
    start = time.perf_counter()
    try:
        yield
    except Exception:
        record_error()
        raise
    finally:
        ms = (time.perf_counter() - start) * 1000
        with _lock:
            _api_timings.append(ms)
            if len(_api_timings) > 500:
                del _api_timings[: len(_api_timings) - 500]
            _api_count += 1


def record_error() -> None:
    global _error_count
    with _lock:
        _error_count += 1


def save_validation(payload: dict[str, Any]) -> None:
    with _lock:
        _last_validation.clear()
        _last_validation.update(payload)


def get_validation() -> dict[str, Any]:
    with _lock:
        return dict(_last_validation)


def save_stress(payload: dict[str, Any]) -> None:
    with _lock:
        _last_stress.clear()
        _last_stress.update(payload)


def get_stress() -> dict[str, Any]:
    with _lock:
        return dict(_last_stress)


def save_scores(payload: dict[str, Any]) -> None:
    with _lock:
        _last_scores.clear()
        _last_scores.update(payload)


def get_scores() -> dict[str, Any]:
    with _lock:
        return dict(_last_scores)


def metrics() -> dict[str, Any]:
    with _lock:
        avg = sum(_api_timings) / len(_api_timings) if _api_timings else 0.0
        return {
            "apiCalls": _api_count,
            "avgLatencyMs": round(avg, 2),
            "errors": _error_count,
        }

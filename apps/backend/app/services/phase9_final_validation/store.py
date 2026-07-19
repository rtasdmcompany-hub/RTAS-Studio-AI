"""In-memory store for Phase 9 final validation runs."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.phase9_final_validation.models import (
        LoadResultRecord,
        ValidationRunRecord,
    )

_lock = threading.RLock()
_runs: OrderedDict[str, "ValidationRunRecord"] = OrderedDict()
_loads: OrderedDict[str, "LoadResultRecord"] = OrderedDict()
_op_timings: list[float] = []
_op_count = 0
_error_count = 0


def reset_store() -> None:
    global _op_count, _error_count
    with _lock:
        _runs.clear()
        _loads.clear()
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
            "validationRuns": len(_runs),
            "loadResults": len(_loads),
        }


def save_run(row: "ValidationRunRecord") -> None:
    with _lock:
        _runs[row.id] = row


def list_runs(*, kind: str | None = None) -> list["ValidationRunRecord"]:
    with _lock:
        return [
            r for r in _runs.values() if kind is None or r.kind == kind
        ]


def save_load(row: "LoadResultRecord") -> None:
    with _lock:
        _loads[row.id] = row


def list_loads() -> list["LoadResultRecord"]:
    with _lock:
        return list(_loads.values())

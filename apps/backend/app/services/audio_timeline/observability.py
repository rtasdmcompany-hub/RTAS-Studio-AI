"""Timeline observability helpers."""

from __future__ import annotations

import time
from typing import Any


def start_timer() -> float:
    return time.perf_counter()


def elapsed_ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000.0, 3)


def log_timeline_event(event: str, **fields: Any) -> dict[str, Any]:
    return {"event": event, "ts": time.time(), **fields}

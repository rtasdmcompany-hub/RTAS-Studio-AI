"""Structured observability for SFX / ambient jobs."""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("rtas.sfx_ambient")


def start_timer() -> float:
    return time.perf_counter()


def elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)


def log_sfx_event(
    event: str,
    *,
    sfx_job_id: str,
    scene_id: str | None = None,
    environment: str | None = None,
    duration_sec: float | None = None,
    processing_time_ms: float | None = None,
    queue_time_ms: float | None = None,
    retry_count: int | None = None,
    error: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event": event,
        "sfx_job_id": sfx_job_id,
        "scene_id": scene_id,
        "environment": environment,
        "duration_sec": duration_sec,
        "processing_time_ms": processing_time_ms,
        "queue_time_ms": queue_time_ms,
        "retry_count": retry_count,
    }
    if error:
        payload["error"] = error
    payload.update({k: v for k, v in extra.items() if v is not None})
    clean = {k: v for k, v in payload.items() if v is not None}
    logger.info("sfx_ambient %s", clean)
    return clean

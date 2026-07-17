"""Structured observability for mix/master jobs."""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("rtas.mixing_mastering")


def start_timer() -> float:
    return time.perf_counter()


def elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)


def log_mix_event(
    event: str,
    *,
    mix_job_id: str,
    master_job_id: str | None = None,
    processing_time_ms: float | None = None,
    queue_time_ms: float | None = None,
    loudness: float | None = None,
    quality_score: float | None = None,
    retry_count: int | None = None,
    error: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event": event,
        "mix_job_id": mix_job_id,
        "master_job_id": master_job_id,
        "processing_time_ms": processing_time_ms,
        "queue_time_ms": queue_time_ms,
        "loudness": loudness,
        "quality_score": quality_score,
        "retry_count": retry_count,
    }
    if error:
        payload["error"] = error
    payload.update({k: v for k, v in extra.items() if v is not None})
    clean = {k: v for k, v in payload.items() if v is not None}
    logger.info("mix_master %s", clean)
    return clean

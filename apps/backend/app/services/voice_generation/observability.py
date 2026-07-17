"""Structured observability for voice generation."""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("rtas.voice_generation")


def start_timer() -> float:
    return time.perf_counter()


def elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)


def log_voice_event(
    event: str,
    *,
    voice_job_id: str | None = None,
    voice_model: str | None = None,
    language: str | None = None,
    duration_sec: float | None = None,
    processing_time_ms: float | None = None,
    queue_time_ms: float | None = None,
    retry_count: int | None = None,
    error: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload = {
        "event": event,
        "voice_job_id": voice_job_id,
        "voice_model": voice_model,
        "language": language,
        "duration": duration_sec,
        "processing_time_ms": processing_time_ms,
        "queue_time_ms": queue_time_ms,
        "retry_count": retry_count,
        "error": error,
        **extra,
    }
    clean = {k: v for k, v in payload.items() if v is not None}
    if error:
        logger.error("voice_generation %s", clean)
    else:
        logger.info("voice_generation %s", clean)
    return clean

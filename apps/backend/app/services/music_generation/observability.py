"""Structured observability for music generation."""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("rtas.music_generation")


def start_timer() -> float:
    return time.perf_counter()


def elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)


def log_music_event(
    event: str,
    *,
    music_job_id: str,
    genre: str | None = None,
    bpm: int | None = None,
    duration_sec: float | None = None,
    mood: str | None = None,
    processing_time_ms: float | None = None,
    queue_time_ms: float | None = None,
    provider: str | None = None,
    retry_count: int | None = None,
    error: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event": event,
        "music_job_id": music_job_id,
        "genre": genre,
        "bpm": bpm,
        "duration": duration_sec,
        "mood": mood,
        "processing_time_ms": processing_time_ms,
        "queue_time_ms": queue_time_ms,
        "provider": provider,
        "retry_count": retry_count,
    }
    if error:
        payload["error"] = error
    payload.update({k: v for k, v in extra.items() if v is not None})
    clean = {k: v for k, v in payload.items() if v is not None}
    logger.info("music_gen %s", clean)
    return clean

"""Structured observability for voice cloning."""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("rtas.voice_cloning")


def start_timer() -> float:
    return time.perf_counter()


def elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)


def log_clone_event(
    event: str,
    *,
    clone_id: str,
    character_id: str | None = None,
    voice_version: int | None = None,
    training_duration_ms: float | None = None,
    processing_time_ms: float | None = None,
    queue_time_ms: float | None = None,
    retry_count: int | None = None,
    provider: str | None = None,
    quality_score: float | None = None,
    error: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event": event,
        "clone_id": clone_id,
        "character_id": character_id,
        "voice_version": voice_version,
        "training_duration_ms": training_duration_ms,
        "processing_time_ms": processing_time_ms,
        "queue_time_ms": queue_time_ms,
        "retry_count": retry_count,
        "provider": provider,
        "quality_score": quality_score,
    }
    if error:
        payload["error"] = error
    payload.update({k: v for k, v in extra.items() if v is not None})
    # Drop Nones for cleaner logs
    clean = {k: v for k, v in payload.items() if v is not None}
    logger.info("voice_clone %s", clean)
    return clean

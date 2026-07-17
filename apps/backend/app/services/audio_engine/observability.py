"""Structured observability for the Audio Production Engine."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.services.audio_engine.models import ObservabilitySnapshot

logger = logging.getLogger("rtas.audio_engine")


def start_timer() -> float:
    return time.perf_counter()


def elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)


def log_event(
    event: str,
    *,
    generation_id: str | None = None,
    job_id: str | None = None,
    provider: str | None = None,
    duration_ms: float | None = None,
    queue_time_ms: float | None = None,
    latency_ms: float | None = None,
    error: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload = {
        "event": event,
        "generation_id": generation_id,
        "job_id": job_id,
        "provider": provider,
        "duration_ms": duration_ms,
        "queue_time_ms": queue_time_ms,
        "latency_ms": latency_ms,
        "error": error,
        **extra,
    }
    # Drop Nones for cleaner structured logs
    clean = {k: v for k, v in payload.items() if v is not None}
    if error:
        logger.error("audio_engine %s", clean)
    else:
        logger.info("audio_engine %s", clean)
    return clean


def build_observability(
    *,
    generation_id: str | None,
    provider: str,
    queue_time_ms: float,
    duration_ms: float,
    events: list[dict[str, Any]],
    errors: list[str] | None = None,
) -> ObservabilitySnapshot:
    return ObservabilitySnapshot(
        generation_id=generation_id,
        provider=provider,
        queue_time_ms=round(queue_time_ms, 3),
        duration_ms=round(duration_ms, 3),
        latency_ms=round(queue_time_ms + duration_ms, 3),
        errors=list(errors or []),
        log_events=list(events),
    )

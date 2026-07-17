"""Structured observability for localization jobs."""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("rtas.localization")


def start_timer() -> float:
    return time.perf_counter()


def elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)


def log_loc_event(
    event: str,
    *,
    translation_job_id: str,
    source_language: str | None = None,
    target_language: str | None = None,
    speaker_count: int | None = None,
    processing_time_ms: float | None = None,
    queue_time_ms: float | None = None,
    retry_count: int | None = None,
    error: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event": event,
        "translation_job_id": translation_job_id,
        "source_language": source_language,
        "target_language": target_language,
        "speaker_count": speaker_count,
        "processing_time_ms": processing_time_ms,
        "queue_time_ms": queue_time_ms,
        "retry_count": retry_count,
    }
    if error:
        payload["error"] = error
    payload.update({k: v for k, v in extra.items() if v is not None})
    clean = {k: v for k, v in payload.items() if v is not None}
    logger.info("localization %s", clean)
    return clean

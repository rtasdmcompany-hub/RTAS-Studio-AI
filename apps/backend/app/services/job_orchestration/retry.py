"""Automatic retry engine with exponential backoff."""

from __future__ import annotations

import random

from app.services.job_orchestration.version import MAX_RETRIES


def can_retry(retry_count: int, max_retries: int | None = None) -> bool:
    limit = MAX_RETRIES if max_retries is None else max_retries
    return retry_count < limit


def backoff_seconds(
    retry_count: int,
    *,
    base: float = 0.05,
    factor: float = 2.0,
    max_delay: float = 5.0,
    jitter: bool = True,
) -> float:
    """Exponential backoff: base * factor^retry_count (+ optional jitter)."""
    delay = min(max_delay, base * (factor ** max(0, retry_count)))
    if jitter:
        delay = delay * (0.75 + random.random() * 0.5)
    return round(delay, 4)

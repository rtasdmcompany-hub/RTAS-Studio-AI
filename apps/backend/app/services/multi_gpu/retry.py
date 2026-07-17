"""Retry policy for Multi GPU jobs."""

from __future__ import annotations

from typing import Any

from app.services.multi_gpu.catalog import preferred_skus
from app.services.multi_gpu.models import GpuSku, MultiGpuJob, RetryPolicy


def default_retry_policy() -> RetryPolicy:
    return RetryPolicy()


def classify_error(error: str | None) -> str:
    e = (error or "").lower()
    if any(x in e for x in ("oom", "out of memory", "cuda oom")):
        return "oom"
    if any(x in e for x in ("timeout", "timed out", "deadline")):
        return "timeout"
    if any(x in e for x in ("worker lost", "heartbeat", "offline", "disconnect")):
        return "worker_lost"
    if any(x in e for x in ("transient", "unavailable", "503", "429")):
        return "transient"
    return "fatal"


def should_retry(job: MultiGpuJob, policy: RetryPolicy, error: str | None) -> bool:
    if job.attempts >= policy.max_attempts:
        return False
    kind = classify_error(error)
    if kind == "fatal":
        return False
    return kind in policy.retry_on


def backoff_ms(job: MultiGpuJob, policy: RetryPolicy) -> int:
    idx = min(max(0, job.attempts - 1), len(policy.backoff_ms) - 1)
    return int(policy.backoff_ms[idx])


def escalate_preferences(job: MultiGpuJob, policy: RetryPolicy) -> list[GpuSku]:
    """On retry, prefer higher-tier SKUs when enabled."""
    if not policy.escalate_sku:
        return list(job.preferred_skus)
    kind = classify_error(job.error)
    min_vram = job.required_vram_mb
    if kind == "oom":
        min_vram = int(job.required_vram_mb * 1.5)
    escalated = preferred_skus(
        quality="cinema" if kind == "oom" else "production",
        require_rt=job.require_rt,
        min_vram_mb=min_vram,
    )
    # Put escalated first, keep originals as fallback
    seen: set[GpuSku] = set()
    out: list[GpuSku] = []
    for s in escalated + list(job.preferred_skus):
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def apply_retry(job: MultiGpuJob, policy: RetryPolicy, error: str | None) -> MultiGpuJob:
    job.attempts += 1
    job.error = error
    job.history.append(
        {
            "event": "retry",
            "attempt": job.attempts,
            "error": error,
            "class": classify_error(error),
            "backoff_ms": backoff_ms(job, policy),
        }
    )
    if should_retry(job, policy, error):
        job.state = "retrying"
        job.preferred_skus = escalate_preferences(job, policy)
        job.assigned_worker_id = None
        job.assigned_sku = None
    else:
        job.state = "failed"
        job.history.append({"event": "give_up", "attempt": job.attempts, "error": error})
    return job


def retry_plan_summary(policy: RetryPolicy) -> dict[str, Any]:
    return {
        "max_attempts": policy.max_attempts,
        "backoff_ms": list(policy.backoff_ms),
        "retry_on": list(policy.retry_on),
        "escalate_sku": policy.escalate_sku,
    }

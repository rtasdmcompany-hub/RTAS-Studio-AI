"""Job Orchestrator — schedule, run, retry, timeout, dependencies."""

from __future__ import annotations

import hashlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from app.services.job_orchestration import store
from app.services.job_orchestration.metrics import compute_metrics
from app.services.job_orchestration.models import (
    TERMINAL_STATES,
    JobMetrics,
    JobPriority,
    JobState,
    OrchestratedJob,
)
from app.services.job_orchestration.queue_manager import queue_manager
from app.services.job_orchestration.retry import backoff_seconds, can_retry
from app.services.job_orchestration.version import (
    DEFAULT_MAX_CONCURRENT,
    DEFAULT_TIMEOUT_SEC,
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    MAX_RETRIES,
)

_lock = threading.Lock()
_running: set[str] = set()
_executor: ThreadPoolExecutor | None = None
_max_concurrent = DEFAULT_MAX_CONCURRENT
_scheduler_started = False


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=_max_concurrent, thread_name_prefix="joborch")
    return _executor


def _job_id(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode()).hexdigest()
    return f"job_{digest[:12]}"


def _resolve_route(prompt: str, request_type: str | None = None) -> tuple[str | None, str | None, str | None]:
    try:
        from app.services.model_routing.engine import select_provider

        sel = select_provider(prompt or "job", request_type=request_type)
        return sel.get("provider"), sel.get("model"), sel.get("request_type")
    except Exception:
        return "simulation", "rtas-sim-universal", request_type or "text"


def _dependencies_met(job: OrchestratedJob) -> bool:
    if not job.depends_on:
        return True
    for dep_id in job.depends_on:
        dep = store.get(dep_id)
        if not dep or dep.state != "completed":
            return False
    return True


def _dependencies_failed(job: OrchestratedJob) -> bool:
    for dep_id in job.depends_on:
        dep = store.get(dep_id)
        if dep and dep.state in ("failed", "cancelled"):
            return True
    return False


def create_job(
    *,
    prompt: str,
    priority: JobPriority = "normal",
    provider: str | None = None,
    model: str | None = None,
    request_type: str | None = None,
    depends_on: list[str] | None = None,
    timeout_sec: float | None = None,
    max_retries: int | None = None,
    metadata: dict[str, Any] | None = None,
    auto_process: bool = True,
) -> dict[str, Any]:
    text = (prompt or "").strip()
    if not text:
        raise ValueError("prompt is required")
    if priority not in ("critical", "high", "normal", "low"):
        raise ValueError("priority must be critical|high|normal|low")

    now = time.time()
    jid = _job_id(text[:80], priority, str(time.time_ns()))
    routed_provider, routed_model, routed_type = _resolve_route(text, request_type)
    job = OrchestratedJob(
        job_id=jid,
        prompt=text,
        state="queued",
        priority=priority,
        provider=provider or routed_provider,
        model=model or routed_model,
        request_type=request_type or routed_type,
        depends_on=list(depends_on or []),
        max_retries=MAX_RETRIES if max_retries is None else int(max_retries),
        timeout_sec=float(timeout_sec or DEFAULT_TIMEOUT_SEC),
        metadata=dict(metadata or {}),
        created_at=now,
        metrics=JobMetrics(provider_used=provider or routed_provider),
    )
    queue_manager.enqueue(job)
    store.save(job)
    if auto_process:
        _ensure_scheduler()
        pump_scheduler()
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "operation": "create",
        **job.to_dict(),
        "queue": queue_manager.statistics(),
    }


def _execute_job(job_id: str) -> None:
    job = store.get(job_id)
    if not job:
        return
    t_proc = time.perf_counter()
    try:
        with _lock:
            _running.add(job_id)
        job.state = "preparing"
        job.progress = 0.1
        job.started_at = time.time()
        if job.enqueued_at:
            job.metrics.queue_time_ms = round((time.perf_counter() - job.enqueued_at) * 1000.0, 3)
        store.save(job)

        # Wait on dependencies
        if job.depends_on:
            job.state = "waiting"
            store.save(job)
            wait_deadline = time.perf_counter() + min(job.timeout_sec, 30.0)
            while time.perf_counter() < wait_deadline:
                if _dependencies_failed(job):
                    raise RuntimeError("dependency_failed")
                if _dependencies_met(job):
                    break
                time.sleep(0.01)
            else:
                if not _dependencies_met(job):
                    raise TimeoutError("dependency_timeout")

        job.state = "running"
        job.progress = 0.35
        store.save(job)

        # Simulate provider work (fast, deterministic)
        # Fail once if metadata force_fail_once and no retries yet
        if job.metadata.get("force_fail_once") and job.retry_count == 0:
            raise RuntimeError("forced_failure_for_retry")

        work_ms = float(job.metadata.get("work_ms") or 5)
        # Cap work for tests/load
        time.sleep(min(0.05, work_ms / 1000.0))

        # Timeout detection
        if job.started_at and (time.time() - job.started_at) > job.timeout_sec:
            raise TimeoutError("job_timeout")

        job.progress = 0.9
        job.result = {
            "ok": True,
            "provider": job.provider,
            "model": job.model,
            "request_type": job.request_type,
            "echo": job.prompt[:120],
        }
        job.state = "completed"
        job.progress = 1.0
        job.error = None
        job.finished_at = time.time()
        job.metrics.processing_time_ms = round((time.perf_counter() - t_proc) * 1000.0, 3)
        job.metrics.total_time_ms = round(
            job.metrics.queue_time_ms + job.metrics.processing_time_ms, 3
        )
        job.metrics.provider_used = job.provider
        job.metrics.retry_count = job.retry_count
        job.metrics.success = True
        job.version += 1
        store.save(job)
    except Exception as exc:
        _fail_or_retry(job_id, str(exc), t_proc)
    finally:
        with _lock:
            _running.discard(job_id)
        pump_scheduler()


def _fail_or_retry(job_id: str, error: str, t_proc: float) -> None:
    job = store.get(job_id)
    if not job or job.state == "cancelled":
        return
    job.error = error
    job.metrics.processing_time_ms = round((time.perf_counter() - t_proc) * 1000.0, 3)
    if can_retry(job.retry_count, job.max_retries):
        job.retry_count += 1
        job.state = "retrying"
        job.progress = 0.0
        job.metrics.retry_count = job.retry_count
        store.save(job)
        delay = backoff_seconds(job.retry_count - 1)
        def _requeue():
            time.sleep(delay)
            current = store.get(job_id)
            if not current or current.state == "cancelled":
                return
            current.state = "retrying"
            queue_manager.enqueue(current)
            store.save(current)
            pump_scheduler()
        threading.Thread(target=_requeue, daemon=True, name=f"retry-{job_id[:8]}").start()
    else:
        job.state = "failed"
        job.finished_at = time.time()
        job.metrics.total_time_ms = round(
            job.metrics.queue_time_ms + job.metrics.processing_time_ms, 3
        )
        job.metrics.provider_used = job.provider
        job.metrics.retry_count = job.retry_count
        job.metrics.success = False
        job.version += 1
        store.save(job)
        # Automatic failed job recovery mark
        job.metadata["recovery_available"] = True
        store.save(job)


def pump_scheduler(max_dispatch: int | None = None) -> int:
    """Job Scheduler — dispatch queued jobs up to concurrency limit."""
    dispatched = 0
    deferred: list[str] = []
    limit = max_dispatch if max_dispatch is not None else _max_concurrent
    scanned = 0
    max_scan = max(limit * 4, 16)
    while dispatched < limit and scanned < max_scan:
        scanned += 1
        with _lock:
            if len(_running) >= _max_concurrent:
                break
        job = queue_manager.dequeue()
        if not job:
            break
        if job.state == "cancelled":
            continue
        if job.depends_on and not _dependencies_met(job) and not _dependencies_failed(job):
            job.state = "waiting"
            store.save(job)
            deferred.append(job.job_id)
            continue
        if _dependencies_failed(job):
            job.state = "failed"
            job.error = "dependency_failed"
            job.finished_at = time.time()
            store.save(job)
            continue
        _get_executor().submit(_execute_job, job.job_id)
        dispatched += 1
    # Re-queue deferred dependency waiters once per pump
    for jid in deferred:
        job = store.get(jid)
        if job and job.state in ("waiting", "queued", "retrying"):
            queue_manager.enqueue(job)
    return dispatched


def _ensure_scheduler() -> None:
    global _scheduler_started
    if _scheduler_started:
        return
    _scheduler_started = True


def get_job(job_id: str) -> dict[str, Any] | None:
    job = store.get(job_id)
    if not job:
        return None
    return {"engine": ENGINE_NAME, "version": ENGINE_VERSION, **job.to_dict()}


def jobs_status() -> dict[str, Any]:
    metrics = compute_metrics()
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "ok": True,
        "max_concurrent": _max_concurrent,
        "active_workers": len(_running),
        **metrics,
    }


def jobs_history(limit: int = 50) -> dict[str, Any]:
    jobs = store.history(limit=limit)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "jobs": [j.summary() for j in jobs],
        "count": len(jobs),
        "metrics": compute_metrics(),
    }


def cancel_job(job_id: str) -> dict[str, Any]:
    job = store.get(job_id)
    if not job:
        raise ValueError(f"Job not found: {job_id}")
    if job.state in TERMINAL_STATES and job.state != "failed":
        if job.state == "completed":
            raise ValueError("Cannot cancel a completed job")
    queue_manager.remove(job_id)
    job.state = "cancelled"
    job.finished_at = time.time()
    job.progress = job.progress
    job.error = job.error or "cancelled_by_user"
    job.metrics.success = False
    store.save(job)
    with _lock:
        _running.discard(job_id)
    return {"engine": ENGINE_NAME, "version": ENGINE_VERSION, "operation": "cancel", **job.to_dict()}


def retry_job(job_id: str) -> dict[str, Any]:
    job = store.get(job_id)
    if not job:
        raise ValueError(f"Job not found: {job_id}")
    if job.state not in ("failed", "cancelled", "completed"):
        # Allow retry of failed/cancelled; completed for recovery tests
        if job.state not in ("failed", "cancelled"):
            raise ValueError(f"Job not retryable in state: {job.state}")
    job.retry_count += 1
    job.state = "retrying"
    job.error = None
    job.progress = 0.0
    job.finished_at = None
    job.started_at = None
    job.metrics.success = False
    job.metadata["manual_retry"] = True
    queue_manager.enqueue(job)
    store.save(job)
    _ensure_scheduler()
    pump_scheduler()
    return {"engine": ENGINE_NAME, "version": ENGINE_VERSION, "operation": "retry", **job.to_dict()}


def wait_for_job(job_id: str, timeout_sec: float = 10.0) -> OrchestratedJob | None:
    deadline = time.perf_counter() + timeout_sec
    while time.perf_counter() < deadline:
        job = store.get(job_id)
        if job and job.state in TERMINAL_STATES:
            return job
        pump_scheduler()
        time.sleep(0.01)
    return store.get(job_id)


def set_max_concurrent(n: int) -> None:
    global _max_concurrent, _executor
    _max_concurrent = max(1, int(n))
    if _executor is not None:
        _executor.shutdown(wait=False, cancel_futures=True)
        _executor = None


def reset_orchestrator() -> None:
    global _scheduler_started, _executor
    queue_manager.clear()
    store.clear()
    with _lock:
        _running.clear()
    if _executor is not None:
        _executor.shutdown(wait=False, cancel_futures=True)
        _executor = None
    _scheduler_started = False


def create_dict(**kwargs: Any) -> dict[str, Any]:
    return create_job(**kwargs)

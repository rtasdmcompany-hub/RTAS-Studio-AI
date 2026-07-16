"""
Real Text-to-Video Engine.

Accepts Production Package JSON → provider requests → queue → metadata → history.
Integrates with Prompt / Director / Shot / Character Memory / Provider Orchestrator.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

from app.services.text_to_video.mapper import map_production_package_to_job
from app.services.text_to_video.models import (
    ProviderGenerationRequest,
    RetryPolicy,
    TextToVideoJob,
)
from app.services.text_to_video.queue import t2v_queue
from app.services.text_to_video.retry import (
    DEFAULT_RETRY_POLICY,
    mark_for_retry,
    next_delay_seconds,
)
from app.services.text_to_video.store import history_store, metadata_store

logger = logging.getLogger(__name__)

GenerateFn = Callable[[ProviderGenerationRequest], Awaitable[dict[str, Any]]]


def build_text_to_video_job(
    production_package: dict[str, Any] | None,
    **kwargs: Any,
) -> TextToVideoJob:
    """Convert a production package into a TextToVideoJob (no side effects)."""
    return map_production_package_to_job(production_package, **kwargs)


def register_job(job: TextToVideoJob, *, enqueue: bool = True) -> TextToVideoJob:
    """Persist job/scene/shot metadata and optionally enqueue provider requests."""
    metadata_store.save_job(job)
    history_store.append(
        job_id=job.job_id,
        event="job_created",
        detail=job.summary(),
    )
    if enqueue and job.requests:
        t2v_queue.enqueue_many(job.requests)
        job.state = "queued"
        metadata_store.save_job(job)
        history_store.append(
            job_id=job.job_id,
            event="requests_queued",
            detail={"count": len(job.requests)},
        )
        for req in job.requests:
            history_store.append(
                job_id=job.job_id,
                request_id=req.request_id,
                event="request_queued",
                detail={
                    "scene_number": req.scene_number,
                    "shot_number": req.shot_number,
                    "duration_seconds": req.duration_seconds,
                },
            )
    return job


def build_and_register_from_intelligence(
    *,
    production_package: dict[str, Any] | None,
    scene_breakdown: dict[str, Any] | None = None,
    character_memory: list[dict[str, Any]] | None = None,
    director_plan: dict[str, Any] | None = None,
    production_render: dict[str, Any] | None = None,
    visual_style: dict[str, Any] | None = None,
    parent_generation_id: str | None = None,
    provider_hint: str | None = None,
    enqueue: bool = True,
) -> TextToVideoJob:
    """Primary integration hook used by the GPU orchestrator."""
    job = build_text_to_video_job(
        production_package,
        scene_breakdown=scene_breakdown,
        character_memory=character_memory,
        director_plan=director_plan,
        production_render=production_render,
        visual_style=visual_style,
        parent_generation_id=parent_generation_id,
        provider_hint=provider_hint,
    )
    return register_job(job, enqueue=enqueue)


def provider_payloads_for_job(job_id: str) -> list[dict[str, Any]]:
    job = metadata_store.get_job(job_id)
    if not job:
        return []
    return [r.to_provider_payload() for r in job.requests]


async def _default_simulate_generate(req: ProviderGenerationRequest) -> dict[str, Any]:
    """Offline generator for tests / dry-run — no cloud calls."""
    await asyncio.sleep(0)
    return {
        "success": True,
        "remote_url": f"https://example.com/t2v/{req.request_id}.mp4",
        "external_job_id": f"sim-{req.request_id}",
        "provider": req.provider_hint or "simulation",
    }


async def process_next_request(
    *,
    generate_fn: GenerateFn | None = None,
    policy: RetryPolicy | None = None,
    sleep_on_retry: bool = False,
) -> ProviderGenerationRequest | None:
    """Dequeue one request and run it through generate_fn with retry support."""
    pol = policy or DEFAULT_RETRY_POLICY
    gen = generate_fn or _default_simulate_generate
    req = t2v_queue.dequeue()
    if not req:
        return None

    history_store.append(
        job_id=req.job_id,
        request_id=req.request_id,
        event="request_started",
        detail={"attempt": req.attempts + 1},
    )
    try:
        result = await gen(req)
    except Exception as exc:  # noqa: BLE001 — convert to retryable failure
        result = {"success": False, "error": str(exc)}

    if result.get("success"):
        updated = t2v_queue.update(
            req.request_id,
            state="completed",
            result_url=result.get("remote_url"),
            external_job_id=result.get("external_job_id"),
            attempts=req.attempts + 1,
            provider=result.get("provider"),
        )
        history_store.append(
            job_id=req.job_id,
            request_id=req.request_id,
            event="request_completed",
            detail={
                "remote_url": result.get("remote_url"),
                "provider": result.get("provider"),
            },
        )
        _refresh_job_state(req.job_id)
        return updated

    error = str(result.get("error") or "generation_failed")
    # Mutate a local copy then sync
    working = t2v_queue.get(req.request_id) or req
    will_retry = mark_for_retry(working, error=error, policy=pol)
    t2v_queue.update(
        req.request_id,
        state=working.state,
        error=error,
        attempts=working.attempts,
    )
    history_store.append(
        job_id=req.job_id,
        request_id=req.request_id,
        event="request_failed",
        detail={"error": error, "will_retry": will_retry, "attempts": working.attempts},
    )
    if will_retry:
        if sleep_on_retry:
            await asyncio.sleep(next_delay_seconds(working, policy=pol))
        t2v_queue.requeue(req.request_id)
        history_store.append(
            job_id=req.job_id,
            request_id=req.request_id,
            event="request_requeued",
            detail={"attempts": working.attempts},
        )
    _refresh_job_state(req.job_id)
    return t2v_queue.get(req.request_id)


async def process_job_queue(
    job_id: str,
    *,
    generate_fn: GenerateFn | None = None,
    policy: RetryPolicy | None = None,
    max_items: int | None = None,
    sleep_on_retry: bool = False,
) -> TextToVideoJob | None:
    """Process queued requests belonging to a job until drained or max_items."""
    metadata_store.update_job_state(job_id, "running")
    history_store.append(job_id=job_id, event="job_running")
    processed = 0
    # Bound loops: each request may retry up to max_attempts
    safety = max(50, (max_items or 200) * 4)
    while safety > 0:
        safety -= 1
        pending = [
            r
            for r in t2v_queue.list_by_job(job_id)
            if r.state in ("queued", "retrying")
        ]
        if not pending:
            break
        nxt = await process_next_request(
            generate_fn=generate_fn,
            policy=policy,
            sleep_on_retry=sleep_on_retry,
        )
        if nxt is None:
            break
        if nxt.job_id != job_id:
            # Foreign request — leave it queued for its own job
            if nxt.state == "running":
                t2v_queue.requeue(nxt.request_id)
            continue
        processed += 1
        if max_items is not None and processed >= max_items:
            break

    return _refresh_job_state(job_id)


def _refresh_job_state(job_id: str) -> TextToVideoJob | None:
    job = metadata_store.get_job(job_id)
    if not job:
        return None
    live = {r.request_id: r for r in t2v_queue.list_by_job(job_id)}
    for i, req in enumerate(job.requests):
        if req.request_id in live:
            job.requests[i] = live[req.request_id]
    states = {r.state for r in job.requests}
    if states and states <= {"completed"}:
        job.state = "completed"
    elif "failed" in states and not ({"queued", "retrying", "running", "planned"} & states):
        if any(r.state == "completed" for r in job.requests):
            job.state = "partial"
        else:
            job.state = "failed"
    elif {"queued", "retrying", "running"} & states:
        job.state = "running" if "running" in states else "queued"
    metadata_store.save_job(job)
    if job.state in ("completed", "failed", "partial"):
        history_store.append(
            job_id=job_id,
            event=f"job_{job.state}",
            detail=job.summary(),
        )
    return job


def get_job(job_id: str) -> dict[str, Any] | None:
    job = metadata_store.get_job(job_id)
    return job.to_dict() if job else None


def get_job_history(job_id: str) -> list[dict[str, Any]]:
    return [h.to_dict() for h in history_store.for_job(job_id)]


def build_text_to_video_dict(
    production_package: dict[str, Any] | None,
    **kwargs: Any,
) -> dict[str, Any]:
    job = build_and_register_from_intelligence(
        production_package=production_package,
        **kwargs,
    )
    return {
        "job": job.to_dict(),
        "summary": job.summary(),
        "provider_payloads": [r.to_provider_payload() for r in job.requests],
        "history": get_job_history(job.job_id),
    }

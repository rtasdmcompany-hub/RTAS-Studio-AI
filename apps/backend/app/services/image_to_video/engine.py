"""
Image-to-Video Engine.

Validates images, merges prompts, maps scenes/providers, queues generation,
supports retry + history. Preserves identity, lighting, composition, environment.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable
from uuid import uuid4

from app.services.image_to_video.metadata import (
    build_image_metadata,
    ingest_image_inputs,
)
from app.services.image_to_video.models import (
    ImageToVideoJob,
    I2VProviderRequest,
    RetryPolicy,
)
from app.services.image_to_video.provider_map import build_provider_requests
from app.services.image_to_video.queue import i2v_queue
from app.services.image_to_video.retry import (
    DEFAULT_RETRY_POLICY,
    mark_for_retry,
    next_delay_seconds,
)
from app.services.image_to_video.scene_map import (
    extract_scenes,
    extract_shots,
    map_images_to_scenes,
)
from app.services.image_to_video.store import history_store, metadata_store
from app.services.image_to_video.validation import validate_images

logger = logging.getLogger(__name__)

GenerateFn = Callable[[I2VProviderRequest], Awaitable[dict[str, Any]]]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_id(parent: str | None, prompt: str) -> str:
    seed = f"{parent or ''}|{prompt}|{uuid4().hex[:8]}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]
    return f"i2v_{digest}"


def build_image_to_video_job(
    *,
    prompt: str,
    images: list[dict[str, Any]] | None = None,
    single_image: str | None = None,
    multiple_images: list[str] | None = None,
    reference_images: list[str] | None = None,
    character_reference: str | None = None,
    product_reference: str | None = None,
    logo_reference: str | None = None,
    production_package: dict[str, Any] | None = None,
    scene_breakdown: dict[str, Any] | None = None,
    character_memory: list[dict[str, Any]] | None = None,
    director_plan: dict[str, Any] | None = None,
    parent_generation_id: str | None = None,
    provider_hint: str | None = None,
    preserve_identity: bool = True,
    preserve_lighting: bool = True,
    preserve_composition: bool = True,
    preserve_environment: bool = True,
    max_attempts: int = 3,
) -> ImageToVideoJob:
    assets = ingest_image_inputs(
        images,
        single_image=single_image,
        multiple_images=multiple_images,
        reference_images=reference_images,
        character_reference=character_reference,
        product_reference=product_reference,
        logo_reference=logo_reference,
    )
    # Pull character refs from memory if none supplied
    if character_memory and not any(a.role == "character" for a in assets):
        for c in character_memory:
            for u in c.get("reference_image_urls") or []:
                if isinstance(u, str) and u.strip():
                    extra = ingest_image_inputs(character_reference=u.strip())
                    assets.extend(extra)
                    break

    validation = validate_images(
        assets,
        require_character_for_identity=preserve_identity,
    )
    preserve = {
        "identity": preserve_identity,
        "lighting": preserve_lighting,
        "composition": preserve_composition,
        "environment": preserve_environment,
    }
    meta_records = build_image_metadata(
        assets,
        preserve_identity=preserve_identity,
        preserve_lighting=preserve_lighting,
        preserve_composition=preserve_composition,
        preserve_environment=preserve_environment,
    )
    job_id = _job_id(parent_generation_id, prompt or "i2v")
    scenes = extract_scenes(production_package, scene_breakdown)
    shots = extract_shots(production_package, scene_breakdown)
    bindings = map_images_to_scenes(assets, scenes, job_id=job_id)
    director_notes = list(
        (director_plan or {}).get("director_notes")
        or (production_package or {}).get("director_notes")
        or []
    )
    requests = build_provider_requests(
        job_id=job_id,
        motion_prompt=prompt
        or str((production_package or {}).get("enhanced_prompt") or ""),
        images=assets,
        bindings=bindings,
        scenes=scenes or [{"scene_number": 1, "estimated_duration_seconds": 5}],
        shots=shots,
        character_memory=character_memory,
        director_notes=director_notes,
        preserve=preserve,
        provider_hint=provider_hint,
        max_attempts=max_attempts,
    )
    ts = _now()
    return ImageToVideoJob(
        job_id=job_id,
        parent_generation_id=parent_generation_id,
        prompt=prompt,
        state="planned",
        images=assets,
        image_metadata=meta_records,
        validation=validation,
        scene_bindings=bindings,
        requests=requests,
        preserve=preserve,
        created_at=ts,
        updated_at=ts,
        metadata={
            "engine": "image_to_video",
            "version": "1.0",
            "image_count": len(assets),
            "roles": sorted({a.role for a in assets}),
        },
    )


def register_job(job: ImageToVideoJob, *, enqueue: bool = True) -> ImageToVideoJob:
    metadata_store.save_job(job)
    history_store.append(job_id=job.job_id, event="job_created", detail=job.summary())
    history_store.append(
        job_id=job.job_id,
        event="validation",
        detail=job.validation.to_dict(),
    )
    if enqueue and job.requests and job.validation.passed:
        i2v_queue.enqueue_many(job.requests)
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
                    "image_url": req.primary_image_url[:120],
                },
            )
    elif not job.validation.passed:
        job.state = "failed"
        metadata_store.save_job(job)
        history_store.append(
            job_id=job.job_id,
            event="job_failed",
            detail={"reason": "validation_failed"},
        )
    return job


def build_and_register(
    *,
    prompt: str,
    enqueue: bool = True,
    **kwargs: Any,
) -> ImageToVideoJob:
    job = build_image_to_video_job(prompt=prompt, **kwargs)
    return register_job(job, enqueue=enqueue)


async def _default_simulate_generate(req: I2VProviderRequest) -> dict[str, Any]:
    await asyncio.sleep(0)
    return {
        "success": True,
        "remote_url": f"https://example.com/i2v/{req.request_id}.mp4",
        "external_job_id": f"sim-{req.request_id}",
        "provider": req.provider_hint or "simulation",
    }


async def process_next_request(
    *,
    generate_fn: GenerateFn | None = None,
    policy: RetryPolicy | None = None,
    sleep_on_retry: bool = False,
) -> I2VProviderRequest | None:
    pol = policy or DEFAULT_RETRY_POLICY
    gen = generate_fn or _default_simulate_generate
    req = i2v_queue.dequeue()
    if not req:
        return None

    history_store.append(
        job_id=req.job_id,
        request_id=req.request_id,
        event="request_started",
        detail={"attempt": req.attempts + 1, "image_url": req.primary_image_url[:120]},
    )
    try:
        result = await gen(req)
    except Exception as exc:  # noqa: BLE001
        result = {"success": False, "error": str(exc)}

    if result.get("success"):
        updated = i2v_queue.update(
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
    working = i2v_queue.get(req.request_id) or req
    will_retry = mark_for_retry(working, error=error, policy=pol)
    i2v_queue.update(
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
        i2v_queue.requeue(req.request_id)
        history_store.append(
            job_id=req.job_id,
            request_id=req.request_id,
            event="request_requeued",
            detail={"attempts": working.attempts},
        )
    _refresh_job_state(req.job_id)
    return i2v_queue.get(req.request_id)


async def process_job_queue(
    job_id: str,
    *,
    generate_fn: GenerateFn | None = None,
    policy: RetryPolicy | None = None,
    max_items: int | None = None,
    sleep_on_retry: bool = False,
) -> ImageToVideoJob | None:
    metadata_store.update_job_state(job_id, "running")
    history_store.append(job_id=job_id, event="job_running")
    processed = 0
    safety = max(50, (max_items or 200) * 4)
    while safety > 0:
        safety -= 1
        pending = [
            r
            for r in i2v_queue.list_by_job(job_id)
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
            if nxt.state == "running":
                i2v_queue.requeue(nxt.request_id)
            continue
        processed += 1
        if max_items is not None and processed >= max_items:
            break
    return _refresh_job_state(job_id)


def _refresh_job_state(job_id: str) -> ImageToVideoJob | None:
    job = metadata_store.get_job(job_id)
    if not job:
        return None
    live = {r.request_id: r for r in i2v_queue.list_by_job(job_id)}
    for i, req in enumerate(job.requests):
        if req.request_id in live:
            job.requests[i] = live[req.request_id]
    states = {r.state for r in job.requests}
    if states and states <= {"completed"}:
        job.state = "completed"
    elif "failed" in states and not ({"queued", "retrying", "running", "planned"} & states):
        job.state = "partial" if any(r.state == "completed" for r in job.requests) else "failed"
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


def provider_payloads_for_job(job_id: str) -> list[dict[str, Any]]:
    job = metadata_store.get_job(job_id)
    if not job:
        return []
    return [r.to_provider_payload() for r in job.requests]


def build_image_to_video_dict(**kwargs: Any) -> dict[str, Any]:
    job = build_and_register(**kwargs)
    return {
        "job": job.to_dict(),
        "summary": job.summary(),
        "provider_payloads": [r.to_provider_payload() for r in job.requests],
        "validation": job.validation.to_dict(),
        "history": get_job_history(job.job_id),
    }

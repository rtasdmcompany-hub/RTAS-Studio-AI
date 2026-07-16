"""API for Real Text-to-Video Engine (backend only — no UI)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.intelligence.pipeline import run_intelligence_pipeline_dict
from app.services.text_to_video import (
    build_and_register_from_intelligence,
    build_text_to_video_dict,
    get_job,
    get_job_history,
    process_job_queue,
    provider_payloads_for_job,
)
from app.services.text_to_video.queue import t2v_queue

router = APIRouter(prefix="/text-to-video", tags=["text-to-video"])


class TextToVideoPlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    category: str | None = None
    visual_style: str | None = Field(None, alias="visualStyle")
    duration_seconds: int | None = Field(None, alias="durationSeconds")
    production_package: dict[str, Any] | None = Field(None, alias="productionPackage")
    enqueue: bool = True
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")

    model_config = {"populate_by_name": True}


class ProcessJobRequest(BaseModel):
    simulate: bool = True
    max_items: int | None = Field(None, alias="maxItems")

    model_config = {"populate_by_name": True}


@router.post("/plan")
async def plan_text_to_video(body: TextToVideoPlanRequest):
    """
    Build scene-by-scene provider requests from a production package
    (or run intelligence pipeline when package is omitted).
    """
    try:
        if body.production_package:
            result = build_text_to_video_dict(
                body.production_package,
                parent_generation_id=body.parent_generation_id,
                enqueue=body.enqueue,
            )
        else:
            plan = run_intelligence_pipeline_dict(
                body.prompt,
                category_hint=body.category,
                style_hint=body.visual_style,
                duration_hint=body.duration_seconds,
            )
            job = build_and_register_from_intelligence(
                production_package=plan.get("production_package"),
                scene_breakdown=plan.get("scene_breakdown"),
                character_memory=plan.get("character_memory"),
                director_plan=plan.get("director_plan"),
                production_render=plan.get("production_render"),
                visual_style=plan.get("visual_style"),
                parent_generation_id=body.parent_generation_id,
                enqueue=body.enqueue,
            )
            result = {
                "job": job.to_dict(),
                "summary": job.summary(),
                "provider_payloads": [r.to_provider_payload() for r in job.requests],
                "history": get_job_history(job.job_id),
            }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, **result}


@router.get("/jobs/{job_id}")
async def get_text_to_video_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Text-to-video job not found")
    return {
        "ok": True,
        "job": job,
        "queue": [r.to_dict() for r in t2v_queue.list_by_job(job_id)],
        "history": get_job_history(job_id),
        "providerPayloads": provider_payloads_for_job(job_id),
    }


@router.get("/jobs/{job_id}/history")
async def get_text_to_video_history(job_id: str):
    return {"ok": True, "jobId": job_id, "history": get_job_history(job_id)}


@router.post("/jobs/{job_id}/process")
async def process_text_to_video_job(job_id: str, body: ProcessJobRequest | None = None):
    """Process queued shot requests (simulate by default — no cloud spend)."""
    opts = body or ProcessJobRequest()
    if not get_job(job_id):
        raise HTTPException(status_code=404, detail="Text-to-video job not found")
    try:
        if opts.simulate:
            job = await process_job_queue(job_id, max_items=opts.max_items)
        else:
            # Live path: use Multi-AI / provider orchestrator per request.
            from app.services.multi_ai import get_multi_ai_engine
            from app.services.ai_service import GenerationJobInput

            engine = get_multi_ai_engine()

            async def live_generate(req):
                job_input = GenerationJobInput(
                    job_id=req.request_id,
                    mode="text-to-video",
                    category="story",
                    visual_style="real",
                    duration_seconds=max(2, int(round(req.duration_seconds))),
                    preview_only=False,
                    use_free_trial=False,
                    main_prompt=req.prompt,
                    compiled_prompt=req.prompt,
                    fields={
                        "rtasShotId": req.shot_id,
                        "rtasSceneNumber": str(req.scene_number),
                        "rtasShotNumber": str(req.shot_number),
                    },
                )
                flow = await engine.generate_with_failover(job_input)
                return {
                    "success": flow.success,
                    "remote_url": flow.remote_url,
                    "external_job_id": flow.external_job_id,
                    "provider": flow.provider,
                    "error": flow.error,
                }

            job = await process_job_queue(
                job_id,
                generate_fn=live_generate,
                max_items=opts.max_items,
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {
        "ok": True,
        "job": job.to_dict() if job else None,
        "history": get_job_history(job_id),
    }


@router.get("/queue")
async def text_to_video_queue_status():
    return {
        "ok": True,
        "size": t2v_queue.size(),
        "peek": [r.to_dict() for r in t2v_queue.peek(limit=25)],
    }

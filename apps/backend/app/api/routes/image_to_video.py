"""API for Image-to-Video Engine (backend only — no UI)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.image_to_video import (
    build_image_to_video_dict,
    get_job,
    get_job_history,
    process_job_queue,
    provider_payloads_for_job,
)
from app.services.image_to_video.queue import i2v_queue

router = APIRouter(prefix="/image-to-video", tags=["image-to-video"])


class ImageToVideoPlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    images: list[dict[str, Any]] | None = None
    single_image: str | None = Field(None, alias="singleImage")
    multiple_images: list[str] | None = Field(None, alias="multipleImages")
    reference_images: list[str] | None = Field(None, alias="referenceImages")
    character_reference: str | None = Field(None, alias="characterReference")
    product_reference: str | None = Field(None, alias="productReference")
    logo_reference: str | None = Field(None, alias="logoReference")
    production_package: dict[str, Any] | None = Field(None, alias="productionPackage")
    scene_breakdown: dict[str, Any] | None = Field(None, alias="sceneBreakdown")
    character_memory: list[dict[str, Any]] | None = Field(None, alias="characterMemory")
    director_plan: dict[str, Any] | None = Field(None, alias="directorPlan")
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")
    enqueue: bool = True
    preserve_identity: bool = Field(True, alias="preserveIdentity")
    preserve_lighting: bool = Field(True, alias="preserveLighting")
    preserve_composition: bool = Field(True, alias="preserveComposition")
    preserve_environment: bool = Field(True, alias="preserveEnvironment")

    model_config = {"populate_by_name": True}


class ProcessJobRequest(BaseModel):
    simulate: bool = True
    max_items: int | None = Field(None, alias="maxItems")

    model_config = {"populate_by_name": True}


@router.post("/plan")
async def plan_image_to_video(body: ImageToVideoPlanRequest):
    try:
        result = build_image_to_video_dict(
            prompt=body.prompt,
            images=body.images,
            single_image=body.single_image,
            multiple_images=body.multiple_images,
            reference_images=body.reference_images,
            character_reference=body.character_reference,
            product_reference=body.product_reference,
            logo_reference=body.logo_reference,
            production_package=body.production_package,
            scene_breakdown=body.scene_breakdown,
            character_memory=body.character_memory,
            director_plan=body.director_plan,
            parent_generation_id=body.parent_generation_id,
            enqueue=body.enqueue,
            preserve_identity=body.preserve_identity,
            preserve_lighting=body.preserve_lighting,
            preserve_composition=body.preserve_composition,
            preserve_environment=body.preserve_environment,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, **result}


@router.get("/jobs/{job_id}")
async def get_image_to_video_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Image-to-video job not found")
    return {
        "ok": True,
        "job": job,
        "queue": [r.to_dict() for r in i2v_queue.list_by_job(job_id)],
        "history": get_job_history(job_id),
        "providerPayloads": provider_payloads_for_job(job_id),
    }


@router.get("/jobs/{job_id}/history")
async def get_image_to_video_history(job_id: str):
    return {"ok": True, "jobId": job_id, "history": get_job_history(job_id)}


@router.post("/jobs/{job_id}/process")
async def process_image_to_video_job(job_id: str, body: ProcessJobRequest | None = None):
    opts = body or ProcessJobRequest()
    if not get_job(job_id):
        raise HTTPException(status_code=404, detail="Image-to-video job not found")
    try:
        if opts.simulate:
            job = await process_job_queue(job_id, max_items=opts.max_items)
        else:
            from app.services.ai_service import GenerationJobInput
            from app.services.multi_ai import get_multi_ai_engine

            engine = get_multi_ai_engine()

            async def live_generate(req):
                job_input = GenerationJobInput(
                    job_id=req.request_id,
                    mode="image",
                    category="story",
                    visual_style="real",
                    duration_seconds=max(2, int(round(req.duration_seconds))),
                    preview_only=False,
                    use_free_trial=False,
                    main_prompt=req.prompt,
                    compiled_prompt=req.prompt,
                    fields={
                        "rtasImageUrl": req.primary_image_url,
                        "rtasSceneNumber": str(req.scene_number),
                        "rtasShotNumber": str(req.shot_number),
                    },
                )
                # Attach public URL onto a lightweight attribute if providers look for it
                setattr(job_input, "source_image_url", req.primary_image_url)
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
async def image_to_video_queue_status():
    return {
        "ok": True,
        "size": i2v_queue.size(),
        "peek": [r.to_dict() for r in i2v_queue.peek(limit=25)],
    }

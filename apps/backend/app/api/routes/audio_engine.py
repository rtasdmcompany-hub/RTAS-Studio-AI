"""API for AI Audio Production Engine (backend only — no UI)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.audio_engine import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    audio_queue,
    build_audio_engine_dict,
    get_plan,
)
from app.services.audio_engine.engine import process_audio_job
from app.services.audio_engine import store

router = APIRouter(prefix="/audio-engine", tags=["audio-engine"])


class AudioEnginePlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    audio_director: dict[str, Any] | None = Field(None, alias="audioDirector")
    lip_sync: dict[str, Any] | None = Field(None, alias="lipSync")
    provider: str = "simulation"
    enqueue: bool = True
    auto_process: bool = Field(True, alias="autoProcess")
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")

    model_config = {"populate_by_name": True}


@router.get("/version")
async def version():
    return {
        "ok": True,
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "phase": "Phase 4",
        "sprint": 1,
    }


@router.post("/plan")
async def plan_audio_engine(body: AudioEnginePlanRequest):
    try:
        result = build_audio_engine_dict(
            body.prompt,
            audio_director=body.audio_director,
            lip_sync=body.lip_sync,
            provider=body.provider,
            enqueue=body.enqueue,
            auto_process=body.auto_process,
            parent_generation_id=body.parent_generation_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, **result}


@router.get("/jobs/{job_id}")
async def get_audio_job(job_id: str):
    plan = get_plan(job_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Audio engine plan not found")
    return {
        "ok": True,
        "plan": plan.to_dict(),
        "summary": plan.summary(),
        "history": store.get_history(job_id),
    }


@router.get("/queue")
async def queue_status():
    return {"ok": True, "queue": audio_queue.status(), "jobs": audio_queue.list_jobs()}


@router.post("/queue/{job_id}/retry")
async def retry_job(job_id: str):
    plan = audio_queue.retry(job_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Audio job not found")
    store.put_plan(plan)
    processed = process_audio_job(job_id) or plan
    return {"ok": True, "summary": processed.summary()}


@router.post("/queue/{job_id}/cancel")
async def cancel_job(job_id: str):
    plan = audio_queue.cancel(job_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Audio job not found")
    store.put_plan(plan)
    return {"ok": True, "summary": plan.summary()}


@router.post("/queue/process-next")
async def process_next():
    nxt = audio_queue.dequeue()
    if not nxt:
        return {"ok": True, "processed": None}
    processed = process_audio_job(nxt.job_id)
    return {
        "ok": True,
        "processed": processed.summary() if processed else nxt.summary(),
    }

"""Multi AI Video Generation Engine API (backend only — no UI)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.multi_ai import get_multi_ai_engine

router = APIRouter(prefix="/multi-ai", tags=["multi-ai"])


class MultiAISelectRequest(BaseModel):
    category: str | None = None
    mood: str | None = None
    preferred_provider: str | None = Field(None, alias="preferredProvider")

    model_config = {"populate_by_name": True}


@router.get("/providers")
async def list_providers():
    engine = get_multi_ai_engine()
    return {
        "ok": True,
        "available": engine.detect_available(),
        "compatibility": engine.compatibility(),
    }


@router.get("/health")
async def multi_ai_health():
    engine = get_multi_ai_engine()
    reports = await engine.health_all()
    return {"ok": True, "providers": reports}


@router.post("/select")
async def select_provider(body: MultiAISelectRequest):
    engine = get_multi_ai_engine()
    selected = engine.select_provider(
        category=body.category,
        mood=body.mood,
        preferred=body.preferred_provider,
    )
    if not selected:
        raise HTTPException(status_code=503, detail="No configured providers")
    adapter = engine.registry[selected]
    return {
        "ok": True,
        "provider": selected,
        "displayName": adapter.display_name,
        "costEstimate": adapter.cost_estimate(5).to_dict(),
        "eta": adapter.eta(5).to_dict(),
        "capability": adapter.capability().to_dict(),
        "failoverAvailable": engine.detect_available(),
    }


@router.get("/queue/{job_id}")
async def queue_progress(job_id: str):
    engine = get_multi_ai_engine()
    job = engine.progress(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Queue job not found")
    return {"ok": True, "job": job.to_dict()}

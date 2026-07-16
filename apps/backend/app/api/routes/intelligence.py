"""Backend API for Real AI intelligence planning (no UI)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.intelligence.pipeline import run_intelligence_pipeline_dict

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


class IntelligencePlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    category: str | None = None
    visual_style: str | None = Field(None, alias="visualStyle")
    duration_seconds: int | None = Field(None, alias="durationSeconds")

    model_config = {"populate_by_name": True}


@router.post("/plan")
async def create_intelligence_plan(body: IntelligencePlanRequest):
    try:
        plan = run_intelligence_pipeline_dict(
            body.prompt,
            category_hint=body.category,
            style_hint=body.visual_style,
            duration_hint=body.duration_seconds,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, "plan": plan}

"""Backend API for Real AI intelligence + director production packages (no UI)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.intelligence.pipeline import run_intelligence_pipeline_dict

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


class IntelligencePlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    category: str | None = None
    visual_style: str | None = Field(None, alias="visualStyle")
    duration_seconds: int | None = Field(None, alias="durationSeconds")
    reference_image_urls: list[str] | None = Field(None, alias="referenceImageUrls")
    character_count: int | None = Field(None, alias="characterCount")
    allow_wardrobe_change: bool = Field(False, alias="allowWardrobeChange")

    model_config = {"populate_by_name": True}


@router.post("/plan")
async def create_intelligence_plan(body: IntelligencePlanRequest):
    try:
        plan = run_intelligence_pipeline_dict(
            body.prompt,
            category_hint=body.category,
            style_hint=body.visual_style,
            duration_hint=body.duration_seconds,
            reference_image_urls=body.reference_image_urls,
            character_count_hint=body.character_count,
            allow_wardrobe_change=body.allow_wardrobe_change,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, "plan": plan}


@router.post("/production-package")
async def create_production_package(body: IntelligencePlanRequest):
    """Full AI production package JSON (Character Memory + Director + Timeline)."""
    try:
        plan = run_intelligence_pipeline_dict(
            body.prompt,
            category_hint=body.category,
            style_hint=body.visual_style,
            duration_hint=body.duration_seconds,
            reference_image_urls=body.reference_image_urls,
            character_count_hint=body.character_count,
            allow_wardrobe_change=body.allow_wardrobe_change,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {
        "ok": True,
        "productionPackage": plan.get("production_package") or plan,
        "characterMemory": plan.get("character_memory"),
        "directorPlan": plan.get("director_plan"),
        "timeline": plan.get("timeline"),
        "continuity": plan.get("continuity"),
        "consistency": plan.get("consistency"),
    }

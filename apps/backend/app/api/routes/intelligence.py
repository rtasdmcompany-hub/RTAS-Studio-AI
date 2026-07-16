"""Backend API for Real AI cinematic brain (no UI)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.intelligence.pipeline import run_intelligence_pipeline_dict
from app.services.intelligence.prompt_intelligence import analyze_prompt
from app.services.intelligence.prompt_understanding import (
    understand_prompt,
    understand_prompt_dict,
)
from app.services.intelligence.character_consistency import run_character_consistency_dict
from app.services.intelligence.character_memory import build_character_memories
from app.services.intelligence.scene_breakdown import (
    build_production_breakdown,
    to_legacy_plans,
)

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


def _run(body: IntelligencePlanRequest) -> dict:
    return run_intelligence_pipeline_dict(
        body.prompt,
        category_hint=body.category,
        style_hint=body.visual_style,
        duration_hint=body.duration_seconds,
        reference_image_urls=body.reference_image_urls,
        character_count_hint=body.character_count,
        allow_wardrobe_change=body.allow_wardrobe_change,
    )


@router.post("/understand")
async def understand_cinematic_prompt(body: IntelligencePlanRequest):
    """Parse a prompt into structured Hollywood production instructions."""
    try:
        understanding = understand_prompt_dict(
            body.prompt, category_hint=body.category
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, "understanding": understanding}


@router.post("/scene-breakdown")
async def create_scene_breakdown(body: IntelligencePlanRequest):
    """Convert one prompt into Scenes[], Shots[], Timeline, Estimated Runtime."""
    try:
        understanding = understand_prompt(
            body.prompt, category_hint=body.category
        )
        intelligence = analyze_prompt(
            body.prompt,
            category_hint=body.category,
            style_hint=body.visual_style,
            duration_hint=body.duration_seconds,
            understanding=understanding,
        )
        production = build_production_breakdown(
            body.prompt,
            understanding=understanding,
            intelligence=intelligence,
        ).to_dict()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, "production": production.get("Production") or production}


@router.post("/character-consistency")
async def create_character_consistency(body: IntelligencePlanRequest):
    """Verify and lock character identity across scenes/shots."""
    try:
        understanding = understand_prompt(
            body.prompt, category_hint=body.category
        )
        intelligence = analyze_prompt(
            body.prompt,
            category_hint=body.category,
            style_hint=body.visual_style,
            duration_hint=body.duration_seconds,
            understanding=understanding,
        )
        characters = build_character_memories(
            body.prompt,
            style_hint=body.visual_style,
            reference_image_urls=body.reference_image_urls,
            character_count_hint=body.character_count,
        )
        breakdown = build_production_breakdown(
            body.prompt,
            understanding=understanding,
            intelligence=intelligence,
            character_name=characters[0].character_id if characters else "lead subject",
        )
        scenes, _cameras, shots = to_legacy_plans(breakdown)
        result = run_character_consistency_dict(
            prompt=body.prompt,
            characters=characters,
            scenes=scenes,
            shots=shots,
            enhanced_prompt=body.prompt,
            understanding=understanding.production_instructions(),
            emotion_hint=intelligence.emotion,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {
        "ok": True,
        "characterConsistency": result,
        "consistencyScore": result.get("consistency_score"),
        "profiles": result.get("profiles"),
    }


@router.post("/plan")
async def create_intelligence_plan(body: IntelligencePlanRequest):
    try:
        plan = _run(body)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, "plan": plan}


@router.post("/production-package")
async def create_production_package(body: IntelligencePlanRequest):
    try:
        plan = _run(body)
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
        "masterAiPlan": plan.get("master_ai_plan"),
        "cinematicQuality": plan.get("cinematic_quality"),
        "promptUnderstanding": plan.get("prompt_understanding"),
        "sceneBreakdown": plan.get("scene_breakdown"),
        "characterConsistency": plan.get("character_consistency"),
    }


@router.post("/master-plan")
async def create_master_ai_plan(body: IntelligencePlanRequest):
    """Hollywood-style master production JSON before generation."""
    try:
        plan = _run(body)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {
        "ok": True,
        "masterAiPlan": plan.get("master_ai_plan"),
        "cinematicReasoning": plan.get("cinematic_reasoning"),
        "visualStyle": plan.get("visual_style"),
        "emotionMap": plan.get("emotion_map"),
        "musicPlan": plan.get("music_plan"),
        "voicePlan": plan.get("voice_plan"),
        "soundPlan": plan.get("sound_plan"),
        "cinematicQuality": plan.get("cinematic_quality"),
        "autoImprovement": plan.get("auto_improvement"),
        "promptUnderstanding": plan.get("prompt_understanding"),
        "sceneBreakdown": plan.get("scene_breakdown"),
        "characterConsistency": plan.get("character_consistency"),
    }

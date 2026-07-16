"""Sprint 4 — Character Memory + AI Director tests (no pydantic required)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEL = ROOT / "app" / "services" / "intelligence"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


models = _load("app.services.intelligence.models", INTEL / "models.py")
director_models = _load(
    "app.services.intelligence.director_models", INTEL / "director_models.py"
)
sys.modules["app.services.intelligence.models"] = models
sys.modules["app.services.intelligence.director_models"] = director_models

for mod_name, file_name in [
    ("prompt_intelligence", "prompt_intelligence.py"),
    ("prompt_enhancer", "prompt_enhancer.py"),
    ("scene_planner", "scene_planner.py"),
    ("camera_planner", "camera_planner.py"),
    ("shot_planner", "shot_planner.py"),
    ("quality_checker", "quality_checker.py"),
    ("export_pipeline", "export_pipeline.py"),
    ("character_memory", "character_memory.py"),
    ("consistency_engine", "consistency_engine.py"),
    ("ai_director", "ai_director.py"),
    ("story_continuity", "story_continuity.py"),
    ("cinematic_timeline", "cinematic_timeline.py"),
    ("production_export", "production_export.py"),
    ("pipeline", "pipeline.py"),
]:
    _load(f"app.services.intelligence.{mod_name}", INTEL / file_name)

character_memory = sys.modules["app.services.intelligence.character_memory"]
consistency_engine = sys.modules["app.services.intelligence.consistency_engine"]
ai_director = sys.modules["app.services.intelligence.ai_director"]
story_continuity = sys.modules["app.services.intelligence.story_continuity"]
pipeline = sys.modules["app.services.intelligence.pipeline"]


def test_character_memory_ids():
    chars = character_memory.build_character_memories(
        "A man and a woman walk through neon city streets",
        style_hint="real",
        reference_image_urls=["https://example.com/face.jpg"],
    )
    assert len(chars) >= 2
    assert chars[0].character_id.startswith("Character_A")
    assert chars[1].character_id.startswith("Character_B")
    assert chars[0].reference_image_urls
    assert "face" in chars[0].locked_traits
    assert chars[0].face_embedding_ref


def test_consistency_locks_identity():
    chars = character_memory.build_character_memories("solo founder in a suit")
    report = consistency_engine.build_consistency_report(chars)
    assert report.face_locked is True
    assert report.hair_locked is True
    assert report.clothing_locked is True
    assert report.body_locked is True
    assert report.proportions_locked is True
    assert chars[0].character_id in report.locked_character_ids


def test_director_and_continuity_and_timeline():
    plan = pipeline.run_intelligence_pipeline(
        "Dramatic story about two characters launching a product at golden hour",
        category_hint="story",
        style_hint="real",
        duration_hint=30,
        character_count_hint=2,
    )
    assert plan.character_memory
    assert plan.consistency.get("face_locked") is True
    assert plan.director_plan.get("shot_order")
    assert plan.director_plan.get("decisions")
    assert plan.continuity.get("time_of_day") in {
        "day",
        "night",
        "golden hour",
        "morning",
    }
    assert plan.timeline.get("nodes")
    kinds = {n["kind"] for n in plan.timeline["nodes"]}
    assert "scene" in kinds and "shot" in kinds
    pkg = plan.production_package
    assert pkg["prompt"]
    assert pkg["enhanced_prompt"]
    assert pkg["character_memory"]
    assert pkg["timeline"]
    assert pkg["director_notes"]
    assert pkg["quality_report"]

    # Continuity: same wardrobe keys for each character
    wardrobe = plan.continuity.get("wardrobe") or {}
    for c in plan.character_memory:
        assert c["character_id"] in wardrobe

    # Scenes reuse character IDs
    for scene in plan.scenes:
        assert scene.characters
        assert all(cid.startswith("Character_") for cid in scene.characters)


if __name__ == "__main__":
    test_character_memory_ids()
    test_consistency_locks_identity()
    test_director_and_continuity_and_timeline()
    print("sprint4 director tests: ok")

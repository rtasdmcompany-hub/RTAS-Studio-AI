"""Sprint 6 — Scene Breakdown & Shot Generation tests (no pydantic)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEL = ROOT / "app" / "services" / "intelligence"
PU = INTEL / "prompt_understanding"
SB = INTEL / "scene_breakdown"

EXAMPLE = (
    "A lonely Pakistani man walks through the rain at night "
    "while remembering his lost love."
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_package(pkg_name: str, pkg_path: Path, modules: list[tuple[str, str]]):
    pkg = type(sys)(pkg_name)
    pkg.__path__ = [str(pkg_path)]
    sys.modules[pkg_name] = pkg
    for mod_name, file_name in modules:
        _load(f"{pkg_name}.{mod_name}", pkg_path / file_name)
    _load(pkg_name, pkg_path / "__init__.py")


models = _load("app.services.intelligence.models", INTEL / "models.py")
sys.modules["app.services.intelligence.models"] = models

_load_package(
    "app.services.intelligence.prompt_understanding",
    PU,
    [
        ("models", "models.py"),
        ("lexicon", "lexicon.py"),
        ("detectors", "detectors.py"),
        ("engine", "engine.py"),
        ("bridge", "bridge.py"),
    ],
)

_load_package(
    "app.services.intelligence.scene_breakdown",
    SB,
    [
        ("models", "models.py"),
        ("shot_catalog", "shot_catalog.py"),
        ("beats", "beats.py"),
        ("pacing", "pacing.py"),
        ("shot_engine", "shot_engine.py"),
        ("engine", "engine.py"),
        ("bridge", "bridge.py"),
    ],
)

pu_engine = sys.modules["app.services.intelligence.prompt_understanding.engine"]
pu_bridge = sys.modules["app.services.intelligence.prompt_understanding.bridge"]
sb_engine = sys.modules["app.services.intelligence.scene_breakdown.engine"]
sb_bridge = sys.modules["app.services.intelligence.scene_breakdown.bridge"]


def test_unit_example_scene_plan():
    understanding = pu_engine.understand_prompt(EXAMPLE)
    intelligence = pu_bridge.to_prompt_intelligence(understanding, language="en")
    breakdown = sb_engine.build_production_breakdown(
        EXAMPLE,
        understanding=understanding,
        intelligence=intelligence,
    )
    titles = [s.title for s in breakdown.scenes]
    assert "Opening Establishing Shot" in titles
    assert "Walking Shot" in titles
    assert "Close Up Face" in titles
    assert "Memory Flashback" in titles
    assert any("Rain" in t or "Detail" in t for t in titles)
    assert "Emotional Ending" in titles
    assert len(breakdown.scenes) >= 6
    print("example_scene_plan=")
    print(json.dumps([s.title for s in breakdown.scenes], indent=2))


def test_unit_shot_fields():
    understanding = pu_engine.understand_prompt(EXAMPLE)
    intelligence = pu_bridge.to_prompt_intelligence(understanding, language="en")
    breakdown = sb_engine.build_production_breakdown(
        EXAMPLE,
        understanding=understanding,
        intelligence=intelligence,
    )
    assert breakdown.shots
    shot = breakdown.shots[0]
    for field in (
        "scene_number",
        "shot_number",
        "shot_type",
        "camera_angle",
        "lens",
        "camera_movement",
        "lighting",
        "environment",
        "weather",
        "time",
        "character_position",
        "character_emotion",
        "facial_expression",
        "body_language",
        "color_palette",
        "depth_of_field",
        "composition",
        "transition_type",
        "sound_design",
        "music_mood",
        "estimated_duration_seconds",
    ):
        assert hasattr(shot, field)
        assert getattr(shot, field) is not None
    prod = breakdown.to_dict()["Production"]
    assert "Scenes" in prod and "Shots" in prod
    assert "Timeline" in prod and "EstimatedRuntime" in prod
    print("example_shot_list=")
    print(json.dumps([s.to_dict() for s in breakdown.shots[:3]], indent=2))


def test_integration_pipeline_compatibility():
    director_models = _load(
        "app.services.intelligence.director_models", INTEL / "director_models.py"
    )
    cinematic_models = _load(
        "app.services.intelligence.cinematic_models", INTEL / "cinematic_models.py"
    )
    sys.modules["app.services.intelligence.director_models"] = director_models
    sys.modules["app.services.intelligence.cinematic_models"] = cinematic_models

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
        ("cinematic_reasoning", "cinematic_reasoning.py"),
        ("visual_style_engine", "visual_style_engine.py"),
        ("emotion_engine", "emotion_engine.py"),
        ("music_planner", "music_planner.py"),
        ("voice_planner", "voice_planner.py"),
        ("sound_design_planner", "sound_design_planner.py"),
        ("cinematic_quality", "cinematic_quality.py"),
        ("auto_improvement", "auto_improvement.py"),
        ("master_ai_plan", "master_ai_plan.py"),
        ("pipeline", "pipeline.py"),
    ]:
        _load(f"app.services.intelligence.{mod_name}", INTEL / file_name)

    pipeline = sys.modules["app.services.intelligence.pipeline"]
    plan = pipeline.run_intelligence_pipeline(EXAMPLE, duration_hint=30)
    assert plan.scene_breakdown.get("Production")
    prod = plan.scene_breakdown["Production"]
    assert len(prod["Scenes"]) >= 6
    assert len(prod["Shots"]) >= 6
    assert prod["EstimatedRuntime"] > 0
    assert plan.character_memory
    assert plan.director_plan
    assert plan.continuity
    assert plan.production_package.get("scene_breakdown")
    # Legacy plans still populated for director/continuity
    assert plan.scenes and plan.shots and plan.cameras


if __name__ == "__main__":
    test_unit_example_scene_plan()
    test_unit_shot_fields()
    test_integration_pipeline_compatibility()
    print("scene breakdown tests: ok")

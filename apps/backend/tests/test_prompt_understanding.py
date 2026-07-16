"""Cinematic Prompt Understanding Engine tests (no pydantic required)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEL = ROOT / "app" / "services" / "intelligence"
PU = INTEL / "prompt_understanding"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# Package scaffolding for importlib
pkg = type(sys)("app.services.intelligence.prompt_understanding")
pkg.__path__ = [str(PU)]
sys.modules["app.services.intelligence.prompt_understanding"] = pkg

_load(
    "app.services.intelligence.prompt_understanding.models",
    PU / "models.py",
)
_load(
    "app.services.intelligence.prompt_understanding.lexicon",
    PU / "lexicon.py",
)
_load(
    "app.services.intelligence.prompt_understanding.detectors",
    PU / "detectors.py",
)
_load(
    "app.services.intelligence.prompt_understanding.engine",
    PU / "engine.py",
)

models = _load("app.services.intelligence.models", INTEL / "models.py")
sys.modules["app.services.intelligence.models"] = models
_load(
    "app.services.intelligence.prompt_understanding.bridge",
    PU / "bridge.py",
)
_load(
    "app.services.intelligence.prompt_understanding",
    PU / "__init__.py",
)

engine = sys.modules["app.services.intelligence.prompt_understanding.engine"]
bridge = sys.modules["app.services.intelligence.prompt_understanding.bridge"]


def test_sad_rain_night_example():
    result = engine.understand_prompt(
        "A sad man walking alone in heavy rain at night."
    )
    data = result.production_instructions()
    assert "Sad" in data["emotion"]
    assert "Lonely" in data["emotion"]
    assert data["weather"] == "Rain"
    assert data["time"] == "Night"
    assert "Low Key" in data["lighting"]
    assert "Blue" in data["lighting"]
    assert "Wet reflections" in data["lighting"]
    assert data["environment"] == "Empty road"
    assert "Slow Dolly" in data["camera"] or "Close Up" in data["camera"]
    assert any("walk" in m.lower() for m in data["movement"])
    assert data["mood"] == "Emotional"
    assert "Piano" in data["music_style"]
    assert "Ambient" in data["music_style"]
    assert "Cold Blue" in data["color_palette"]
    for key in (
        "scene_type",
        "camera",
        "lighting",
        "lens",
        "movement",
        "environment",
        "mood",
        "emotion",
        "weather",
        "time",
        "color_palette",
        "music_style",
        "transition_style",
    ):
        assert key in data and data[key] is not None


def test_category_detection_matrix():
    cases = {
        "Music Video": "cinematic music video performance on stage",
        "Advertisement": "luxury brand advertisement for a new perfume",
        "Documentary": "documentary interview in a real world factory",
        "Islamic Video": "islamic video about prayer at the mosque",
        "Podcast": "podcast host interview episode intro",
        "Product Video": "product video demo of a smartwatch tabletop",
        "Anime": "anime fight scene with cel shaded characters",
        "TikTok": "tiktok dance hook vertical video",
        "Trailer": "epic movie trailer smash cuts",
    }
    for expected, prompt in cases.items():
        got = engine.understand_prompt(prompt).category
        assert got == expected, f"{prompt!r} -> {got!r}, expected {expected!r}"


def test_bridge_keeps_legacy_intelligence_contract():
    understanding = engine.understand_prompt(
        "A sad man walking alone in heavy rain at night."
    )
    intel = bridge.to_prompt_intelligence(understanding, language="en")
    assert intel.category  # legacy field present
    assert intel.emotion == "somber"
    assert intel.camera_requirements
    assert "Low Key" in intel.lighting or "Blue" in intel.lighting
    assert 0.0 < intel.confidence <= 1.0


def test_pipeline_compatibility():
    # Load full pipeline stack for director/memory compatibility
    director_models = _load(
        "app.services.intelligence.director_models", INTEL / "director_models.py"
    )
    cinematic_models = _load(
        "app.services.intelligence.cinematic_models", INTEL / "cinematic_models.py"
    )
    sys.modules["app.services.intelligence.director_models"] = director_models
    sys.modules["app.services.intelligence.cinematic_models"] = cinematic_models

    SB = INTEL / "scene_breakdown"
    sb_pkg = type(sys)("app.services.intelligence.scene_breakdown")
    sb_pkg.__path__ = [str(SB)]
    sys.modules["app.services.intelligence.scene_breakdown"] = sb_pkg
    for sb_name, sb_file in [
        ("models", "models.py"),
        ("shot_catalog", "shot_catalog.py"),
        ("beats", "beats.py"),
        ("pacing", "pacing.py"),
        ("shot_engine", "shot_engine.py"),
        ("engine", "engine.py"),
        ("bridge", "bridge.py"),
    ]:
        _load(f"app.services.intelligence.scene_breakdown.{sb_name}", SB / sb_file)
    _load("app.services.intelligence.scene_breakdown", SB / "__init__.py")

    CC = INTEL / "character_consistency"
    cc_pkg = type(sys)("app.services.intelligence.character_consistency")
    cc_pkg.__path__ = [str(CC)]
    sys.modules["app.services.intelligence.character_consistency"] = cc_pkg
    for cc_name, cc_file in [
        ("models", "models.py"),
        ("subject_detector", "subject_detector.py"),
        ("embeddings", "embeddings.py"),
        ("identity_builder", "identity_builder.py"),
        ("verifier", "verifier.py"),
        ("corrector", "corrector.py"),
        ("bridge", "bridge.py"),
        ("engine", "engine.py"),
    ]:
        _load(f"app.services.intelligence.character_consistency.{cc_name}", CC / cc_file)
    _load("app.services.intelligence.character_consistency", CC / "__init__.py")

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
    plan = pipeline.run_intelligence_pipeline(
        "A sad man walking alone in heavy rain at night.",
        duration_hint=20,
    )
    assert plan.prompt_understanding.get("weather") == "Rain"
    assert plan.character_memory  # Character Memory compatible
    assert plan.director_plan  # Director compatible
    assert plan.continuity  # Continuity compatible
    print("example_parsed_json=")
    print(json.dumps(plan.prompt_understanding, indent=2))


if __name__ == "__main__":
    test_sad_rain_night_example()
    test_category_detection_matrix()
    test_bridge_keeps_legacy_intelligence_contract()
    test_pipeline_compatibility()
    print("prompt understanding tests: ok")

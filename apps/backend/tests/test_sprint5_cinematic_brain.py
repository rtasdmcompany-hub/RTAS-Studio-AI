"""Sprint 5 — Cinematic AI Brain tests (no pydantic required)."""

from __future__ import annotations

import importlib.util
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


models = _load("app.services.intelligence.models", INTEL / "models.py")
director_models = _load(
    "app.services.intelligence.director_models", INTEL / "director_models.py"
)
cinematic_models = _load(
    "app.services.intelligence.cinematic_models", INTEL / "cinematic_models.py"
)
sys.modules["app.services.intelligence.models"] = models
sys.modules["app.services.intelligence.director_models"] = director_models
sys.modules["app.services.intelligence.cinematic_models"] = cinematic_models

# Prompt Understanding package (required by prompt_intelligence)
pu_pkg = type(sys)("app.services.intelligence.prompt_understanding")
pu_pkg.__path__ = [str(PU)]
sys.modules["app.services.intelligence.prompt_understanding"] = pu_pkg
for pu_name, pu_file in [
    ("models", "models.py"),
    ("lexicon", "lexicon.py"),
    ("detectors", "detectors.py"),
    ("engine", "engine.py"),
    ("bridge", "bridge.py"),
]:
    _load(f"app.services.intelligence.prompt_understanding.{pu_name}", PU / pu_file)
_load("app.services.intelligence.prompt_understanding", PU / "__init__.py")

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

AD = INTEL / "audio_director"
ad_pkg = type(sys)("app.services.intelligence.audio_director")
ad_pkg.__path__ = [str(AD)]
sys.modules["app.services.intelligence.audio_director"] = ad_pkg
for ad_name, ad_file in [
    ("models", "models.py"),
    ("detectors", "detectors.py"),
    ("timelines", "timelines.py"),
    ("lip_sync", "lip_sync.py"),
    ("bridge", "bridge.py"),
    ("engine", "engine.py"),
]:
    _load(f"app.services.intelligence.audio_director.{ad_name}", AD / ad_file)
_load("app.services.intelligence.audio_director", AD / "__init__.py")

PR = INTEL / "production_render"
pr_pkg = type(sys)("app.services.intelligence.production_render")
pr_pkg.__path__ = [str(PR)]
sys.modules["app.services.intelligence.production_render"] = pr_pkg
for pr_name, pr_file in [
    ("models", "models.py"),
    ("export_specs", "export_specs.py"),
    ("captions", "captions.py"),
    ("assets", "assets.py"),
    ("validator", "validator.py"),
    ("engine", "engine.py"),
]:
    _load(f"app.services.intelligence.production_render.{pr_name}", PR / pr_file)
_load("app.services.intelligence.production_render", PR / "__init__.py")

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
cinematic_quality = sys.modules["app.services.intelligence.cinematic_quality"]
auto_improvement = sys.modules["app.services.intelligence.auto_improvement"]
cinematic_models_mod = sys.modules["app.services.intelligence.cinematic_models"]


def test_cinematic_reasoning_and_master_plan():
    plan = pipeline.run_intelligence_pipeline(
        "Luxury brand commercial about a founder launching a watch at golden hour",
        category_hint="business",
        style_hint="real",
        duration_hint=30,
    )
    assert plan.cinematic_reasoning.get("story")
    assert plan.cinematic_reasoning.get("audience")
    assert plan.visual_style.get("reference_look") in {
        "Hollywood",
        "Netflix",
        "Apple TV+",
        "IMAX",
        "Commercial",
        "Music Video",
        "Documentary",
        "Anime",
        "Luxury Brand",
    }
    assert plan.emotion_map.get("beats")
    assert plan.music_plan.get("tempo_bpm")
    assert plan.voice_plan.get("language")
    assert plan.sound_plan.get("ambient")
    master = plan.master_ai_plan
    for key in (
        "project_summary",
        "story_analysis",
        "character_memory",
        "scene_plan",
        "shot_plan",
        "camera_plan",
        "lighting_plan",
        "music_plan",
        "voice_plan",
        "sound_plan",
        "timeline",
        "quality_report",
        "export_plan",
    ):
        assert key in master and master[key] is not None


def test_quality_engine_and_auto_improve():
    # Force a weak prompt to encourage improvement path.
    plan = pipeline.run_intelligence_pipeline("ad", category_hint="business", duration_hint=15)
    score = plan.cinematic_quality
    assert "overall" in score
    assert 0.0 <= float(score["overall"]) <= 1.0
    assert "story" in score and "camera" in score and "emotion" in score
    # Short prompt should often trigger auto improvement.
    assert plan.auto_improvement.get("intent_preserved") is True
    assert plan.enhancement.enhanced_prompt


if __name__ == "__main__":
    test_cinematic_reasoning_and_master_plan()
    test_quality_engine_and_auto_improve()
    print("sprint5 cinematic brain tests: ok")

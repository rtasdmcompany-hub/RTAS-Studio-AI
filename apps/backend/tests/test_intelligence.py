"""Tests for Real AI intelligence modules (no pydantic / FastAPI required)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEL = ROOT / "app" / "services" / "intelligence"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Pre-import the real intelligence package in correct dependency order so the
# manual importlib reloads below cannot trigger a partial-init circular import
# (prompt_intelligence -> prompt_understanding -> intelligence/__init__ -> pipeline).
import app.services.intelligence  # noqa: E402,F401


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

prompt_intelligence = sys.modules["app.services.intelligence.prompt_intelligence"]
pipeline = sys.modules["app.services.intelligence.pipeline"]


def test_prompt_intelligence_structured():
    result = prompt_intelligence.analyze_prompt(
        "Cinematic commercial for a luxury watch at golden hour with slow push-in",
        category_hint="business",
        style_hint="real",
        duration_hint=15,
    )
    data = result.to_dict()
    assert data["language"] == "en"
    assert data["category"] == "business"
    assert data["style"] == "real"
    assert "camera_requirements" in data
    assert data["estimated_duration_seconds"] == 15
    assert isinstance(data["missing_information"], list)


def test_full_intelligence_pipeline():
    plan = pipeline.run_intelligence_pipeline(
        "Dramatic story about a founder launching a product in neon city lights",
        category_hint="story",
        style_hint="real",
        duration_hint=30,
    )
    assert plan.enhancement.intent_preserved is True
    assert plan.enhancement.original_prompt
    assert plan.enhancement.enhanced_prompt
    assert len(plan.scenes) >= 2
    assert len(plan.cameras) == len(plan.scenes)
    assert len(plan.shots) >= len(plan.scenes)
    assert plan.export.format == "mp4"
    assert isinstance(plan.quality.passed, bool)
    assert plan.character_memory
    assert plan.production_package
    payload = plan.to_dict()
    assert "intelligence" in payload and "shots" in payload
    assert "character_memory" in payload


if __name__ == "__main__":
    test_prompt_intelligence_structured()
    test_full_intelligence_pipeline()
    print("intelligence tests: ok")

"""Tests for Real AI intelligence modules (no pydantic / FastAPI required)."""

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


# Load package modules without importing app.services.__init__ (pydantic).
models = _load("rtas_intel_models", INTEL / "models.py")
sys.modules["app.services.intelligence.models"] = models
prompt_intelligence = _load(
    "app.services.intelligence.prompt_intelligence", INTEL / "prompt_intelligence.py"
)
prompt_enhancer = _load(
    "app.services.intelligence.prompt_enhancer", INTEL / "prompt_enhancer.py"
)
scene_planner = _load(
    "app.services.intelligence.scene_planner", INTEL / "scene_planner.py"
)
camera_planner = _load(
    "app.services.intelligence.camera_planner", INTEL / "camera_planner.py"
)
shot_planner = _load(
    "app.services.intelligence.shot_planner", INTEL / "shot_planner.py"
)
quality_checker = _load(
    "app.services.intelligence.quality_checker", INTEL / "quality_checker.py"
)
export_pipeline = _load(
    "app.services.intelligence.export_pipeline", INTEL / "export_pipeline.py"
)
pipeline = _load("app.services.intelligence.pipeline", INTEL / "pipeline.py")


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
    payload = plan.to_dict()
    assert "intelligence" in payload and "shots" in payload


if __name__ == "__main__":
    test_prompt_intelligence_structured()
    test_full_intelligence_pipeline()
    print("intelligence tests: ok")

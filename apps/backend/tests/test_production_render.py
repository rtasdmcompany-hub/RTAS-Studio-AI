"""Sprint 10 — Production Render & Export Engine tests."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEL = ROOT / "app" / "services" / "intelligence"
PU = INTEL / "prompt_understanding"
SB = INTEL / "scene_breakdown"
CC = INTEL / "character_consistency"
AD = INTEL / "audio_director"
PR = INTEL / "production_render"

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


def _load_pkg(pkg_name: str, pkg_path: Path, modules: list[tuple[str, str]]):
    pkg = type(sys)(pkg_name)
    pkg.__path__ = [str(pkg_path)]
    sys.modules[pkg_name] = pkg
    for mod_name, file_name in modules:
        _load(f"{pkg_name}.{mod_name}", pkg_path / file_name)
    _load(pkg_name, pkg_path / "__init__.py")


models = _load("app.services.intelligence.models", INTEL / "models.py")
sys.modules["app.services.intelligence.models"] = models
director_models = _load(
    "app.services.intelligence.director_models", INTEL / "director_models.py"
)
sys.modules["app.services.intelligence.director_models"] = director_models
cinematic_models = _load(
    "app.services.intelligence.cinematic_models", INTEL / "cinematic_models.py"
)
sys.modules["app.services.intelligence.cinematic_models"] = cinematic_models

_load_pkg(
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
_load_pkg(
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
_load_pkg(
    "app.services.intelligence.character_consistency",
    CC,
    [
        ("models", "models.py"),
        ("subject_detector", "subject_detector.py"),
        ("embeddings", "embeddings.py"),
        ("identity_builder", "identity_builder.py"),
        ("verifier", "verifier.py"),
        ("corrector", "corrector.py"),
        ("bridge", "bridge.py"),
        ("engine", "engine.py"),
    ],
)
_load_pkg(
    "app.services.intelligence.audio_director",
    AD,
    [
        ("models", "models.py"),
        ("detectors", "detectors.py"),
        ("timelines", "timelines.py"),
        ("lip_sync", "lip_sync.py"),
        ("bridge", "bridge.py"),
        ("engine", "engine.py"),
    ],
)
_load_pkg(
    "app.services.intelligence.production_render",
    PR,
    [
        ("models", "models.py"),
        ("export_specs", "export_specs.py"),
        ("captions", "captions.py"),
        ("assets", "assets.py"),
        ("validator", "validator.py"),
        ("engine", "engine.py"),
    ],
)

char_mem = _load(
    "app.services.intelligence.character_memory", INTEL / "character_memory.py"
)
pr_engine = sys.modules["app.services.intelligence.production_render.engine"]
pr_specs = sys.modules["app.services.intelligence.production_render.export_specs"]
pu_engine = sys.modules["app.services.intelligence.prompt_understanding.engine"]
pu_bridge = sys.modules["app.services.intelligence.prompt_understanding.bridge"]
sb_engine = sys.modules["app.services.intelligence.scene_breakdown.engine"]
sb_bridge = sys.modules["app.services.intelligence.scene_breakdown.bridge"]
ad_engine = sys.modules["app.services.intelligence.audio_director.engine"]


def _build_context():
    understanding = pu_engine.understand_prompt(EXAMPLE)
    intelligence = pu_bridge.to_prompt_intelligence(understanding, language="en")
    characters = char_mem.build_character_memories(EXAMPLE, style_hint="real")
    breakdown = sb_engine.build_production_breakdown(
        EXAMPLE, understanding=understanding, intelligence=intelligence
    )
    scenes, cameras, shots = sb_bridge.to_legacy_plans(breakdown)
    audio = ad_engine.build_audio_director_plan(
        EXAMPLE,
        intelligence=intelligence,
        scenes=scenes,
        understanding=understanding.production_instructions(),
        character_memory=[c.to_dict() for c in characters],
    )
    return (
        understanding,
        intelligence,
        characters,
        scenes,
        cameras,
        shots,
        audio,
        breakdown,
    )


def test_export_matrix_covers_formats_aspects_hdr_8k():
    understanding = pu_engine.understand_prompt(EXAMPLE)
    intelligence = pu_bridge.to_prompt_intelligence(understanding, language="en")
    specs = pr_specs.build_export_specs(
        intelligence, understanding=understanding.production_instructions()
    )
    formats = {s.format for s in specs}
    aspects = {s.aspect for s in specs}
    resolutions = {s.resolution for s in specs}
    assert formats >= {"mp4", "mov", "webm"}
    assert aspects >= {"vertical", "landscape", "square"}
    assert "8k_ready" in resolutions
    assert any(s.resolution == "4k" or s.resolution == "1080p" for s in specs)
    assert any(s.hdr for s in specs)
    primary = pr_specs.primary_export_spec(specs)
    assert primary.format == "mp4"


def test_production_package_assemblies():
    (
        understanding,
        intelligence,
        characters,
        scenes,
        cameras,
        shots,
        audio,
        breakdown,
    ) = _build_context()
    pkg = pr_engine.build_production_render(
        prompt=EXAMPLE,
        enhanced_prompt=EXAMPLE + " cinematic",
        intelligence=intelligence,
        scenes=scenes,
        shots=shots,
        cameras=cameras,
        character_memory=[c.to_dict() for c in characters],
        director_plan={
            "transition_style": "motivated cut",
            "director_notes": ["Protect face identity", "Rain continuity"],
        },
        timeline={"total_duration_seconds": 24, "beats": []},
        understanding=understanding.production_instructions(),
        audio_director=audio.to_dict(),
        music_plan={"genre": "ambient"},
        voice_plan={"language": "en"},
        sound_plan={"ambience": "rain"},
        visual_style={"color_palette": ["teal", "amber"], "lighting": "neon wet"},
        scene_breakdown=breakdown.to_dict(),
        character_consistency={"consistency_score": {"overall": 0.9}},
        continuity={"locks": ["rain"]},
        quality_report={"passed": True, "score": 0.9},
    )
    d = pkg.to_dict()
    assert d["json_package"]["scenes"]
    assert d["json_package"]["shots"]
    assert d["timeline"]
    assert d["assets"]
    assert d["video_manifest"]["tracks"]["captions"]["format"] == "srt"
    assert "-->" in d["subtitle_file"]
    assert d["thumbnail_instructions"]
    assert d["voice_package"]["lip_sync_timeline"]
    assert d["music_package"]["timeline"]
    assert d["camera_plan"]
    assert d["director_notes"]
    assert d["transitions"] is not None
    assert d["effects"]
    assert d["validation"]["passed"] is True
    assert d["validation"]["checks"]["export_mp4"]
    assert d["validation"]["checks"]["has_8k_ready"]

    export_plan = pr_engine.to_export_plan(pkg)
    assert export_plan.format in ("mp4", "mov", "webm")
    assert export_plan.resolution in ("720p", "1080p", "4k")
    print("export_package_example=")
    print(
        json.dumps(
            {
                "video_manifest": d["video_manifest"],
                "export_specs": d["export_specs"][:3],
                "validation": d["validation"],
                "subtitle_preview": d["subtitle_file"][:200],
            },
            indent=2,
        )
    )
    print("production_manifest_example=")
    print(json.dumps(d["video_manifest"], indent=2))


def test_pipeline_integration():
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
    plan = pipeline.run_intelligence_pipeline(EXAMPLE, duration_hint=24)
    assert plan.production_render
    assert plan.production_render.get("validation", {}).get("passed") is True
    assert plan.production_render.get("video_manifest")
    assert plan.production_render.get("subtitle_file")
    assert plan.production_package.get("production_render")
    assert plan.production_package.get("export_validation")
    assert plan.master_ai_plan.get("production_render")
    assert plan.export.format
    assert any(
        s.get("format") == "mp4" for s in plan.production_render.get("export_specs") or []
    )


if __name__ == "__main__":
    test_export_matrix_covers_formats_aspects_hdr_8k()
    test_production_package_assemblies()
    test_pipeline_integration()
    print("production render tests: ok")

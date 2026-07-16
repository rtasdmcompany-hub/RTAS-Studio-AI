"""Sprint 9 — AI Audio Director & Lip Sync Engine tests."""

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

char_mem = _load(
    "app.services.intelligence.character_memory", INTEL / "character_memory.py"
)
ad_engine = sys.modules["app.services.intelligence.audio_director.engine"]
pu_engine = sys.modules["app.services.intelligence.prompt_understanding.engine"]
pu_bridge = sys.modules["app.services.intelligence.prompt_understanding.bridge"]
sb_engine = sys.modules["app.services.intelligence.scene_breakdown.engine"]
sb_bridge = sys.modules["app.services.intelligence.scene_breakdown.bridge"]


def test_audio_timelines_and_detection():
    understanding = pu_engine.understand_prompt(EXAMPLE)
    intelligence = pu_bridge.to_prompt_intelligence(understanding, language="en")
    characters = char_mem.build_character_memories(EXAMPLE, style_hint="real")
    breakdown = sb_engine.build_production_breakdown(
        EXAMPLE, understanding=understanding, intelligence=intelligence
    )
    scenes, _c, _s = sb_bridge.to_legacy_plans(breakdown)
    plan = ad_engine.build_audio_director_plan(
        EXAMPLE,
        intelligence=intelligence,
        scenes=scenes,
        understanding=understanding.production_instructions(),
        character_memory=[c.to_dict() for c in characters],
    )
    d = plan.detection
    assert d.language in ("en", "ur")
    assert d.accent
    assert d.gender in ("male", "female", "neutral")
    assert d.emotion
    assert d.speech_speed
    assert d.pause_timing
    assert d.music_style
    assert "voice" in d.volume_balance
    assert plan.voice_timeline
    assert plan.music_timeline
    assert plan.sfx_timeline
    assert plan.estimated_runtime_seconds > 0
    print("audio_timeline_example=")
    print(json.dumps([c.to_dict() for c in plan.voice_timeline[:2]], indent=2))
    print(json.dumps([c.to_dict() for c in plan.music_timeline[:2]], indent=2))
    print(json.dumps([c.to_dict() for c in plan.sfx_timeline[:2]], indent=2))


def test_lip_sync_timeline():
    understanding = pu_engine.understand_prompt(EXAMPLE)
    intelligence = pu_bridge.to_prompt_intelligence(understanding, language="en")
    characters = char_mem.build_character_memories(EXAMPLE)
    breakdown = sb_engine.build_production_breakdown(
        EXAMPLE, understanding=understanding, intelligence=intelligence
    )
    scenes, _c, _s = sb_bridge.to_legacy_plans(breakdown)
    plan = ad_engine.build_audio_director_plan(
        EXAMPLE,
        intelligence=intelligence,
        scenes=scenes,
        understanding=understanding.production_instructions(),
        character_memory=[c.to_dict() for c in characters],
    )
    assert plan.lip_sync_timeline
    cue = plan.lip_sync_timeline[0]
    assert cue.character_id
    assert cue.viseme
    assert cue.phoneme_hint
    assert 0.0 <= cue.mouth_openness <= 1.0
    assert cue.dialogue_snippet
    assert cue.sync_confidence > 0
    print("lip_sync_example=")
    print(json.dumps([c.to_dict() for c in plan.lip_sync_timeline[:4]], indent=2))


def test_category_matrix():
    cases = {
        "music_video": "cinematic music video performance with lyrics",
        "advertisement": "luxury brand advertisement product demo",
        "podcast": "podcast host interview episode intro",
        "islamic": "islamic video about prayer at the mosque",
        "shorts": "tiktok vertical short hook",
        "documentary": "documentary interview in a real world factory",
    }
    for expected, prompt in cases.items():
        understanding = pu_engine.understand_prompt(prompt)
        intelligence = pu_bridge.to_prompt_intelligence(understanding, language="en")
        scenes_dummy = [
            models.ScenePlan(
                index=0,
                title="Opening",
                duration_seconds=5,
                description=prompt,
                environment="set",
                characters=["lead"],
                actions=["talk"],
                transitions="cut",
            )
        ]
        plan = ad_engine.build_audio_director_plan(
            prompt,
            intelligence=intelligence,
            scenes=scenes_dummy,
            understanding=understanding.production_instructions(),
        )
        assert plan.detection.category == expected, (
            f"{prompt!r} -> {plan.detection.category}, expected {expected}"
        )


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
    assert plan.audio_director.get("lip_sync_timeline")
    assert plan.audio_director.get("voice_timeline")
    assert plan.music_plan.get("genre")
    assert plan.voice_plan.get("language")
    assert plan.production_package.get("audio_director")
    assert plan.director_plan
    assert plan.character_memory


if __name__ == "__main__":
    test_audio_timelines_and_detection()
    test_lip_sync_timeline()
    test_category_matrix()
    test_pipeline_integration()
    print("audio director tests: ok")

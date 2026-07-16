"""Sprint 8 — Character Consistency Engine tests (no pydantic)."""

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

char_mem = _load("app.services.intelligence.character_memory", INTEL / "character_memory.py")
cc_engine = sys.modules["app.services.intelligence.character_consistency.engine"]
subject_detector = sys.modules[
    "app.services.intelligence.character_consistency.subject_detector"
]
embeddings = sys.modules["app.services.intelligence.character_consistency.embeddings"]
sb_engine = sys.modules["app.services.intelligence.scene_breakdown.engine"]
pu_engine = sys.modules["app.services.intelligence.prompt_understanding.engine"]
pu_bridge = sys.modules["app.services.intelligence.prompt_understanding.bridge"]


def test_subject_kinds():
    assert subject_detector.detect_subject_kind("a man walks alone") == "single_character"
    assert subject_detector.detect_subject_kind("a couple walks together", 2) == "two_characters"
    assert subject_detector.detect_subject_kind("a family at dinner") == "family"
    assert subject_detector.detect_subject_kind("a crowd cheers") == "crowd"
    assert subject_detector.detect_subject_kind("a dog runs in a field") == "animal"
    assert (
        subject_detector.detect_subject_kind("a parked sports car vehicle hero shot")
        == "vehicle"
    )


def test_embedding_stability():
    v1, ref1 = embeddings.build_face_embedding(
        subject_id="Character_A",
        reference_image_urls=["https://example.com/face.jpg"],
        traits_fingerprint="short|adult|medium-brown|brown|suit",
    )
    v2, ref2 = embeddings.build_face_embedding(
        subject_id="Character_A",
        reference_image_urls=["https://example.com/face.jpg"],
        traits_fingerprint="short|adult|medium-brown|brown|suit",
    )
    assert ref1 == ref2
    assert embeddings.cosine_similarity(v1, v2) > 0.99
    assert len(v1) == embeddings.EMBEDDING_DIM


def test_consistency_score_and_locks():
    understanding = pu_engine.understand_prompt(EXAMPLE)
    intelligence = pu_bridge.to_prompt_intelligence(understanding, language="en")
    characters = char_mem.build_character_memories(
        EXAMPLE,
        style_hint="real",
        reference_image_urls=["https://example.com/pakistani-man.jpg"],
    )
    breakdown = sb_engine.build_production_breakdown(
        EXAMPLE,
        understanding=understanding,
        intelligence=intelligence,
    )
    scenes, _cams, shots = sys.modules[
        "app.services.intelligence.scene_breakdown.bridge"
    ].to_legacy_plans(breakdown)

    result, scenes2, shots2, prompt2 = cc_engine.run_character_consistency(
        prompt=EXAMPLE,
        characters=characters,
        scenes=scenes,
        shots=shots,
        enhanced_prompt=EXAMPLE,
        understanding=understanding.production_instructions(),
        emotion_hint=intelligence.emotion,
    )
    assert result.subject_kind == "single_character"
    assert result.profiles
    profile = result.profiles[0]
    for trait in (
        "identity",
        "face",
        "hair",
        "age",
        "body",
        "clothes",
        "pose",
        "expression",
        "voice",
        "walking_style",
        "skin_tone",
        "eye_color",
        "lighting_adaptation",
    ):
        assert getattr(profile, trait)
    assert profile.face_embedding
    assert result.embedding_ready
    score = result.verification.score
    assert 0.0 <= score.overall <= 1.0
    assert score.face >= 0.7
    assert "IDENTITY LOCK" in prompt2
    assert "no face swapping" in prompt2.lower()
    assert all("identity lock" in (s.description or "").lower() for s in scenes2)
    print("character_consistency_example=")
    print(json.dumps(result.profiles[0].to_dict(), indent=2)[:1200])
    print("consistency_score_example=")
    print(json.dumps(score.to_dict(), indent=2))


def test_pipeline_integration():
    cinematic_models = _load(
        "app.services.intelligence.cinematic_models", INTEL / "cinematic_models.py"
    )
    sys.modules["app.services.intelligence.cinematic_models"] = cinematic_models
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
    plan = pipeline.run_intelligence_pipeline(EXAMPLE, duration_hint=24)
    assert plan.character_consistency.get("consistency_score")
    assert plan.character_consistency["verification"]["passed"] is True
    assert plan.character_memory
    assert plan.director_plan
    assert plan.consistency.get("face_locked") is True


if __name__ == "__main__":
    test_subject_kinds()
    test_embedding_stability()
    test_consistency_score_and_locks()
    test_pipeline_integration()
    print("character consistency tests: ok")

"""Phase 5 Sprint 8 — AI Cinematic Environment & World Generation Engine tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WI = ROOT / "app" / "services" / "world_intelligence"
CG = ROOT / "app" / "services" / "character_generation"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _ensure_parents(pkg_name: str):
    parts = pkg_name.split(".")
    for i in range(1, len(parts)):
        parent = ".".join(parts[:i])
        if parent not in sys.modules:
            mod = type(sys)(parent)
            mod.__path__ = []
            sys.modules[parent] = mod
    if "app" in sys.modules:
        sys.modules["app"].__path__ = [str(ROOT / "app")]
    if "app.services" in sys.modules:
        sys.modules["app.services"].__path__ = [str(ROOT / "app" / "services")]


def _load_pkg(pkg_name: str, pkg_path: Path, modules: list[tuple[str, str]]):
    _ensure_parents(pkg_name)
    if pkg_name in sys.modules and all(
        f"{pkg_name}.{mod_name}" in sys.modules for mod_name, _ in modules
    ):
        return
    pkg = type(sys)(pkg_name)
    pkg.__path__ = [str(pkg_path)]
    sys.modules[pkg_name] = pkg
    for mod_name, file_name in modules:
        _load(f"{pkg_name}.{mod_name}", pkg_path / file_name)


_load_pkg(
    "app.services.character_generation",
    CG,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("templates", "templates.py"),
        ("validation", "validation.py"),
        ("paddle_status", "paddle_status.py"),
        ("registry", "registry.py"),
        ("store", "store.py"),
        ("engine", "engine.py"),
    ],
)

_load_pkg(
    "app.services.world_intelligence",
    WI,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("library", "library.py"),
        ("analysis", "analysis.py"),
        ("builders", "builders.py"),
        ("consistency", "consistency.py"),
        ("bridge", "bridge.py"),
        ("store", "store.py"),
        ("queue", "queue.py"),
        ("engine", "engine.py"),
    ],
)

version = sys.modules["app.services.world_intelligence.version"]
library = sys.modules["app.services.world_intelligence.library"]
analysis = sys.modules["app.services.world_intelligence.analysis"]
builders = sys.modules["app.services.world_intelligence.builders"]
consistency = sys.modules["app.services.world_intelligence.consistency"]
store = sys.modules["app.services.world_intelligence.store"]
queue_mod = sys.modules["app.services.world_intelligence.queue"]
engine = sys.modules["app.services.world_intelligence.engine"]
cg_paddle = sys.modules["app.services.character_generation.paddle_status"]


def setup_function():
    store.clear()
    queue_mod.world_queue.clear()
    consistency.clear_memory()


def test_version_unit():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 5
    assert version.SPRINT == 8


def test_environment_library_unit():
    lib = library.list_world_library()
    assert lib["environment_count"] >= 24
    assert lib["weather_count"] >= 12
    assert lib["lighting_count"] >= 7
    assert lib["extensible"] is True
    ids = {e["environment_id"] for e in lib["environments"]}
    for required in (
        "city",
        "village",
        "forest",
        "desert",
        "mountains",
        "snow",
        "ocean",
        "beach",
        "river",
        "space",
        "office",
        "home",
        "school",
        "hospital",
        "factory",
        "restaurant",
        "airport",
        "hotel",
        "shopping_mall",
        "stadium",
        "historical",
        "futuristic",
        "fantasy",
        "custom",
    ):
        assert required in ids
    library.register_environment("neon_bazaar", {"category": "urban", "assets": ["stalls", "neon"]})
    assert library.resolve_environment("neon_bazaar") == "neon_bazaar"


def test_weather_mood_sync_unit():
    assert library.weather_for_mood("sad") == "rain"
    assert library.weather_for_mood("romantic") == "golden_hour"
    assert library.weather_for_mood("angry") == "thunderstorm"
    result = analysis.analyze_world("A quiet garden", mood="fear")
    assert result.recommended_weather == "fog"


def test_lighting_profiles_unit():
    for lid in (
        "natural_light",
        "studio_light",
        "soft_light",
        "hard_light",
        "rim_light",
        "cinematic_light",
        "hdr_lighting",
    ):
        profile = builders.build_lighting(lid)
        assert profile.lighting_id == lid
        assert profile.shadows
        assert profile.gi_strength >= 0
        assert profile.reflections >= 0
    cinematic = builders.build_lighting("cinematic_light")
    assert cinematic.rim is True
    assert cinematic.hdr is True


def test_environment_builder_unit():
    bp = builders.build_environment(
        world_id="w1",
        environment="forest",
        weather="fog",
        time_of_day="blue_hour",
        mood="suspense",
    )
    assert bp.environment_id == "forest"
    assert bp.location_id.startswith("loc_")
    assert bp.weather.weather_id == "fog"
    assert "trees" in bp.assets["background_objects"] or bp.assets["trees"] is True
    assert bp.lighting.lighting_id


def test_world_analysis_unit():
    result = analysis.analyze_world(
        "Rainy city streets at night with neon signs.",
        mood="suspense",
    )
    assert result.recommended_environment == "city"
    assert result.recommended_weather in ("rain", "night")
    assert result.confidence > 0.5


def test_generate_integration_and_bridges():
    result = engine.generate_world(
        prompt="A cinematic beach at golden hour, romantic atmosphere.",
        world_id="world_beach_1",
        scene_id="scene_01",
        environment="beach",
        mood="romantic",
        story_plan={"title": "Sunset"},
        director_plan={"plan_id": "dir_w1"},
        scene_plan={"scene_id": "scene_01"},
        camera_plan={"job_id": "cam_w1"},
        character_dna={"character_id": "char_1"},
        motion_plan={"job_id": "mot_w1"},
        emotion_plan={"job_id": "emo_w1"},
        timeline_plan={"timeline_id": "tl1"},
        audio_summary={"ambience": "waves"},
    )
    assert result["state"] == "completed"
    assert result["environment_blueprint"]["environment_id"] == "beach"
    assert result["consistency"]["consistent"] is True
    assert result["consistency"]["no_continuity_breaks"] is True
    assert result["integrations"]["story_engine"]["linked"] is True
    assert result["integrations"]["director_engine"]["linked"] is True
    assert result["integrations"]["scene_planner"]["linked"] is True
    assert result["integrations"]["camera_engine"]["linked"] is True
    assert result["integrations"]["character_dna"]["linked"] is True
    assert result["integrations"]["motion_engine"]["linked"] is True
    assert result["integrations"]["emotion_engine"]["linked"] is True
    assert result["integrations"]["timeline_engine"]["linked"] is True
    assert result["integrations"]["audio_engine"]["linked"] is True
    assert result["observability"]["weather_type"]
    assert result["observability"]["lighting_profile"]
    fetched = engine.get_world(result["job_id"])
    assert fetched is not None


def test_world_consistency_across_scenes():
    first = engine.generate_world(
        prompt="Dense forest with misty paths.",
        world_id="world_forest_lock",
        scene_id="s1",
        environment="forest",
        weather="fog",
    )
    assert first["consistent"] is True
    loc1 = first["environment_blueprint"]["location_id"]
    env1 = first["environment_blueprint"]["environment_id"]
    second = engine.generate_world(
        prompt="Same forest, light rain begins as mood turns sad.",
        world_id="world_forest_lock",
        scene_id="s2",
        environment="forest",
        mood="sad",
    )
    assert second["environment_blueprint"]["location_id"] == loc1
    assert second["environment_blueprint"]["environment_id"] == env1
    assert second["consistency"]["consistent"] is True
    assert second["consistency"]["no_continuity_breaks"] is True
    assert second["consistency"]["score"] >= version.WORLD_CONSISTENCY_THRESHOLD


def test_queue_states_and_create_then_generate():
    created = engine.create_world(
        prompt="Desert dunes under bright sun.",
        environment="desert",
        weather="sunny",
    )
    assert created["state"] == "queued"
    assert created["queue"]["queued"] >= 1
    generated = engine.generate_world(job_id=created["job_id"])
    assert generated["state"] == "completed"
    assert generated["environment_blueprint"]["environment_id"] == "desert"
    hist = engine.world_history(limit=10)
    assert hist["count"] >= 1
    lib = engine.world_library_payload()
    assert lib["environment_count"] >= 24


def test_consistency_verify_unit():
    bp = builders.build_environment(
        world_id="wc1",
        environment="city",
        weather="cloudy",
        time_of_day="day",
    )
    report = consistency.verify_consistency("wc1", bp)
    assert report.consistent is True
    assert report.score >= 80
    drifted = builders.build_environment(
        world_id="wc1",
        environment="city",
        weather="rain",
        time_of_day="night",
    )
    drifted.location_id = "loc_different"
    bad = consistency.verify_consistency("wc1", bp, drifted)
    assert bad.consistent is False
    assert bad.drift_flags


def test_stress_and_performance_budget():
    t0 = time.perf_counter()
    envs = ["city", "forest", "beach", "office", "fantasy", "space", "stadium", "hospital"]
    scores = []
    for i, env in enumerate(envs * 3):
        result = engine.generate_world(
            prompt=f"Generate {env} environment scene {i}",
            world_id=f"stress_world_{env}",
            environment=env,
            scene_id=f"sc_{i}",
        )
        assert result["state"] == "completed"
        scores.append(result["consistency"]["score"])
    elapsed = time.perf_counter() - t0
    assert elapsed < 8.0
    assert min(scores) >= version.WORLD_CONSISTENCY_THRESHOLD
    assert all(s >= 80 for s in scores)


def test_paddle_secrets_not_exposed():
    status = cg_paddle.paddle_status()
    assert isinstance(status, dict)
    blob = str(status)
    assert "sk_" not in blob

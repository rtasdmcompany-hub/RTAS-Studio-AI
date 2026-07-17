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
    for required in ("city", "forest", "desert", "space", "office", "fantasy", "custom"):
        assert required in ids
    library.register_environment("neon_bay", {"category": "sci_fi", "assets": ["neon", "water"]})
    assert library.resolve_environment("neon_bay") == "neon_bay"


def test_weather_mood_sync_unit():
    assert library.weather_for_mood("sad") == "rain"
    assert library.weather_for_mood("romantic") == "golden_hour"
    assert library.weather_for_mood("angry") == "thunderstorm"
    result = analysis.analyze_world("A quiet street", mood="fear")
    assert result.recommended_weather == "fog"


def test_lighting_engine_unit():
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
        assert profile.gi_strength > 0
        assert profile.reflections >= 0
    cinematic = builders.build_lighting("cinematic_light")
    assert cinematic.rim is True
    assert cinematic.hdr is True


def test_environment_generation_unit():
    env = builders.build_environment(
        world_id="w1",
        environment="forest",
        weather="fog",
        time_of_day="blue_hour",
        mood="suspense",
    )
    assert env.environment_id == "forest"
    assert env.weather.weather_id == "fog"
    assert env.assets["trees"] is True
    assert env.lighting.lighting_id


def test_world_analysis_unit():
    result = analysis.analyze_world(
        "Cyber neon futuristic city at night with thunderstorm",
        mood="suspense",
    )
    assert result.recommended_environment in ("city", "futuristic")
    assert result.recommended_weather in ("thunderstorm", "night")
    assert result.confidence > 0.5


def test_generate_integration():
    result = engine.generate_world(
        prompt="Rainy city streets at night with neon reflections.",
        world_id="world_int_1",
        scene_id="scene_1",
        mood="sad",
        story_plan={"id": "s1"},
        director_plan={"plan_id": "d1"},
        scene_plan={"scene_id": "scene_1"},
        camera_plan={"job_id": "cam1"},
        character_dna={"character_id": "c1"},
        motion_plan={"job_id": "mot1"},
        emotion_plan={"emotion": "sad"},
        timeline_plan={"id": "t1"},
        audio_summary={"ambience": "rain"},
    )
    assert result["state"] == "completed"
    assert result["environment_blueprint"]["environment_id"] == "city"
    assert result["environment_blueprint"]["weather"]["weather_id"] in ("rain", "night", "cloudy")
    assert result["integrations"]["story_engine"]["linked"] is True
    assert result["integrations"]["camera_engine"]["linked"] is True
    assert result["integrations"]["emotion_engine"]["linked"] is True
    assert result["observability"]["weather_type"]
    assert result["observability"]["lighting_profile"]
    assert "_plans" not in result.get("metadata", {})
    fetched = engine.get_world(result["job_id"])
    assert fetched is not None
    hist = engine.world_history(limit=10)
    assert hist["count"] >= 1
    lib = engine.world_library_payload()
    assert lib["environment_count"] >= 24


def test_world_consistency():
    first = engine.generate_world(
        prompt="A quiet forest clearing in soft fog.",
        world_id="world_consistency_1",
        scene_id="sc_a",
        environment="forest",
        weather="fog",
    )
    assert first["consistency"]["consistent"] is True
    assert first["consistency"]["score"] >= 80
    loc1 = first["environment_blueprint"]["location_id"]
    second = engine.generate_world(
        prompt="Same forest, light rain begins to fall.",
        world_id="world_consistency_1",
        scene_id="sc_b",
        mood="sad",
    )
    assert second["environment_blueprint"]["environment_id"] == "forest"
    assert second["environment_blueprint"]["location_id"] == loc1
    assert second["consistency"]["no_continuity_breaks"] is True
    assert second["consistency"]["consistent"] is True
    report = second["consistency"]
    for trait in (
        "location",
        "buildings",
        "roads",
        "trees",
        "background_objects",
        "sky",
        "weather",
        "time_of_day",
        "lighting",
        "environmental_assets",
    ):
        assert trait in report["preserved_traits"]


def test_queue_states():
    created = engine.create_world(prompt="Desert dunes under harsh sun.", environment="desert")
    assert created["state"] == "queued"
    status = queue_mod.world_queue.status()
    assert status["queued"] >= 1
    processed = engine.process_world_job(created["job_id"])
    assert processed is not None
    assert processed.state == "completed"
    assert processed.observability is not None
    assert processed.observability.processing_time_ms >= 0


def test_create_then_generate():
    created = engine.create_world(
        prompt="Beach golden hour romantic sunset",
        environment="beach",
        mood="romantic",
    )
    generated = engine.generate_world(job_id=created["job_id"])
    assert generated["state"] == "completed"
    assert generated["environment_blueprint"]["environment_id"] == "beach"


def test_stress_and_performance_budget():
    envs = ["city", "forest", "desert", "ocean", "office", "space", "fantasy", "stadium"]
    t0 = time.perf_counter()
    scores = []
    for env in envs * 3:
        result = engine.generate_world(
            prompt=f"Cinematic {env} environment scene",
            world_id=f"stress_{env}",
            environment=env,
        )
        assert result["state"] == "completed"
        scores.append(result["consistency"]["score"])
    elapsed = time.perf_counter() - t0
    assert elapsed < 8.0
    assert min(scores) >= 80
    assert all(s >= 80 for s in scores)


def test_paddle_secrets_not_exposed():
    status = cg_paddle.paddle_status()
    assert isinstance(status, dict)
    for key, value in status.items():
        if isinstance(value, str):
            assert "sk_" not in value.lower()
            assert "secret" not in value.lower() or value in ("configured", "missing", "present", "absent")

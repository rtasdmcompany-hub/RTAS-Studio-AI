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
    library.register_environment("neon_alley", {"category": "urban", "assets": ["neon", "alleys"]})
    assert library.resolve_environment("neon_alley") == "neon_alley"


def test_weather_mood_sync_unit():
    sad = analysis.analyze_world("A quiet street.", mood="sad")
    assert sad.recommended_weather == "rain"
    romantic = analysis.analyze_world("A quiet street.", mood="romantic")
    assert romantic.recommended_weather == "golden_hour"
    forest = analysis.analyze_world("Deep forest woods with mist and fog among trees.")
    assert forest.recommended_environment == "forest"


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
        assert profile.gi_strength >= 0
        assert profile.reflections >= 0
    env = builders.build_environment(
        world_id="w1",
        environment="city",
        weather="night",
        time_of_day="night",
        mood="suspense",
    )
    assert env.lighting.lighting_id in (
        "cinematic_light",
        "soft_light",
        "hdr_lighting",
        "rim_light",
        "natural_light",
        "hard_light",
    )
    assert env.weather.weather_id == "night"


def test_generate_integration_and_bridges():
    result = engine.generate_world(
        prompt="Rainy city streets at night near downtown skyline.",
        world_id="world_int_1",
        scene_id="scene_1",
        mood="suspense",
        story_plan={"beats": 3},
        director_plan={"plan_id": "dir_w1"},
        scene_plan={"shots": 4},
        camera_plan={"job_id": "cam_w1"},
        character_dna={"character_id": "char_w1"},
        motion_plan={"job_id": "mot_w1"},
        emotion_plan={"job_id": "emo_w1"},
        timeline_plan={"clips": 2},
        audio_summary={"ambience": "rain"},
    )
    assert result["state"] == "completed"
    assert result["environment_blueprint"]["environment_id"] == "city"
    assert result["consistency"]["consistent"] is True
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
    hist = engine.world_history(limit=10)
    assert hist["count"] >= 1
    lib = engine.world_library_payload()
    assert lib["environment_count"] >= 24


def test_world_consistency_across_scenes():
    first = engine.generate_world(
        prompt="A coastal beach with sand and palms at golden hour.",
        world_id="world_cont_1",
        scene_id="s1",
        environment="beach",
    )
    assert first["state"] == "completed"
    loc1 = first["environment_blueprint"]["location_id"]
    env1 = first["environment_blueprint"]["environment_id"]
    second = engine.generate_world(
        prompt="Same beach later as the mood turns romantic.",
        world_id="world_cont_1",
        scene_id="s2",
        mood="romantic",
    )
    assert second["environment_blueprint"]["location_id"] == loc1
    assert second["environment_blueprint"]["environment_id"] == env1
    assert second["consistency"]["consistent"] is True
    assert second["consistency"]["no_continuity_breaks"] is True
    assert second["consistency"]["score"] >= version.WORLD_CONSISTENCY_THRESHOLD
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


def test_queue_states_unit():
    created = engine.create_world(prompt="Office interior daytime meeting room.")
    assert created["state"] == "queued"
    job_id = created["job_id"]
    processed = engine.process_world_job(job_id)
    assert processed is not None
    assert processed.state == "completed"
    status = queue_mod.world_queue.status()
    assert "queued" in status["states"]
    assert status["states"]["completed"] >= 1


def test_stress_and_performance_budget():
    t0 = time.perf_counter()
    envs = ["city", "forest", "desert", "hospital", "fantasy", "space", "beach", "factory"]
    scores = []
    for env in envs * 2:
        result = engine.generate_world(
            prompt=f"Cinematic {env} environment establishing shot.",
            world_id=f"stress_{env}",
            environment=env,
        )
        assert result["state"] == "completed"
        scores.append(result["consistency"]["score"])
    elapsed = time.perf_counter() - t0
    assert elapsed < 8.0
    assert min(scores) >= version.WORLD_CONSISTENCY_THRESHOLD


def test_paddle_secrets_not_exposed():
    status = cg_paddle.paddle_status()
    assert isinstance(status, dict)
    blob = str(status).lower()
    assert "sk_" not in blob
    assert "api_key" not in blob or status.get("configured") is not None

"""Phase 5 Sprint 6 — AI Cinematic Camera & Shot Intelligence Engine tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / "app" / "services" / "camera_intelligence"
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
    "app.services.camera_intelligence",
    CI,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("library", "library.py"),
        ("planning", "planning.py"),
        ("bridge", "bridge.py"),
        ("store", "store.py"),
        ("queue", "queue.py"),
        ("engine", "engine.py"),
    ],
)

version = sys.modules["app.services.camera_intelligence.version"]
library = sys.modules["app.services.camera_intelligence.library"]
planning = sys.modules["app.services.camera_intelligence.planning"]
store = sys.modules["app.services.camera_intelligence.store"]
queue_mod = sys.modules["app.services.camera_intelligence.queue"]
engine = sys.modules["app.services.camera_intelligence.engine"]
cg_paddle = sys.modules["app.services.character_generation.paddle_status"]


def setup_function():
    store.clear()
    queue_mod.camera_queue.clear()


def test_version_unit():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 5
    assert version.SPRINT == 6


def test_library_shots_and_lenses_unit():
    lib = library.list_camera_library()
    assert lib["shot_count"] >= 21
    assert lib["lens_count"] >= 6
    assert lib["extensible"] is True
    ids = {s["shot_id"] for s in lib["shots"]}
    for required in (
        "extreme_wide_shot",
        "close_up",
        "tracking_shot",
        "dolly_shot",
        "crane_shot",
        "orbit_shot",
        "cinematic_reveal",
        "pov",
        "drone_shot",
    ):
        assert required in ids
    library.register_shot("macro_insert", {"category": "custom", "focal_hint": 100})
    assert library.resolve_shot("macro_insert") == "macro_insert"
    lens = library.select_lens_for_shot("close_up")
    assert lens.focal_length_mm >= 70


def test_scene_analysis_unit():
    analysis = planning.analyze_scene(
        "An epic city skyline at dawn establishing the story, suspense builds",
        character_ids=["a", "b"],
    )
    assert analysis.scene_type in ("establishing", "reveal")
    assert analysis.character_count == 2
    assert analysis.camera_movement_recommendation
    assert analysis.lighting
    action = planning.analyze_scene("A fast chase fight action sequence in the streets")
    assert action.scene_type == "action"


def test_shot_planning_unit():
    analysis = planning.analyze_scene("Two people argue in a quiet room", character_ids=["c1", "c2"])
    seq = planning.recommend_shot_sequence(analysis, max_shots=4)
    assert len(seq) >= 3
    shot = planning.build_shot(seq[0], analysis, job_id="j1", index=0, start_sec=0.0)
    assert shot.framing["shot_size"]
    assert shot.composition["rule_of_thirds"] is True
    assert shot.camera_motion["face_tracking"] is True
    assert shot.auto_focus is True
    assert shot.lens.lens_id


def test_plan_and_generate_integration():
    planned = engine.plan_camera(
        prompt="Cinematic dialogue between two leads in a rainy city, serious mood",
        scene_id="scene_01",
        character_ids=["char_a", "char_b"],
        director_plan={"plan_id": "dir_1"},
        motion_plan={"job_id": "cmotion_1"},
        audio_summary={"dialogue": True},
    )
    assert planned["state"] == "queued"
    assert planned["analysis"]["character_count"] == 2
    generated = engine.generate_camera(job_id=planned["job_id"])
    assert generated["state"] == "completed"
    assert generated["shot_count"] >= 3
    assert generated["coverage"]["complete"] is True
    assert generated["integrations"]["director_engine"]["linked"] is True
    assert generated["integrations"]["motion_engine"]["linked"] is True
    assert generated["observability"]["processing_time_ms"] >= 0
    assert generated["shots"][0]["face_tracking"] is True
    fetched = engine.get_camera(planned["job_id"])
    assert fetched is not None
    assert fetched["job_id"] == planned["job_id"]


def test_preset_and_history():
    result = engine.generate_camera(
        prompt="Epic establishing drone over mountains",
        preset="epic_establish",
        duration_sec=12.0,
    )
    assert result["state"] == "completed"
    types = [s["shot_type"] for s in result["shots"]]
    assert "extreme_wide_shot" in types or "drone_shot" in types
    hist = engine.camera_history(limit=10)
    assert hist["count"] >= 1


def test_performance_under_budget():
    t0 = time.perf_counter()
    for i in range(5):
        engine.generate_camera(
            prompt=f"Action chase scene number {i}",
            max_shots=3,
            duration_sec=6.0,
        )
    assert (time.perf_counter() - t0) < 5.0


def test_paddle_still_works():
    status = cg_paddle.paddle_status()
    assert status["secrets_exposed"] is False
    assert all(isinstance(v, bool) for v in status["env_presence"].values())

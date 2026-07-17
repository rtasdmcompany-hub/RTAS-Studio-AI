"""Phase 5 Sprint 5 — AI Character Motion & Cinematic Animation Engine tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CM = ROOT / "app" / "services" / "character_motion"
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
    "app.services.character_motion",
    CM,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("library", "library.py"),
        ("emotion", "emotion.py"),
        ("engines", "engines.py"),
        ("profile", "profile.py"),
        ("bridge", "bridge.py"),
        ("store", "store.py"),
        ("queue", "queue.py"),
        ("engine", "engine.py"),
    ],
)

version = sys.modules["app.services.character_motion.version"]
models = sys.modules["app.services.character_motion.models"]
library = sys.modules["app.services.character_motion.library"]
emotion = sys.modules["app.services.character_motion.emotion"]
engines = sys.modules["app.services.character_motion.engines"]
profile = sys.modules["app.services.character_motion.profile"]
store = sys.modules["app.services.character_motion.store"]
queue_mod = sys.modules["app.services.character_motion.queue"]
engine = sys.modules["app.services.character_motion.engine"]
cg_engine = sys.modules["app.services.character_generation.engine"]
cg_store = sys.modules["app.services.character_generation.store"]
cg_registry = sys.modules["app.services.character_generation.registry"]
cg_paddle = sys.modules["app.services.character_generation.paddle_status"]


def setup_function():
    store.clear()
    queue_mod.motion_queue.clear()
    cg_store.clear()
    cg_registry.clear()


def test_version_unit():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 5
    assert version.SPRINT == 5


def test_pose_and_motion_engines_unit():
    bias = emotion.emotion_movement_bias("excited")
    poses = engines.build_pose_sequence("walking", 3.0, bias)
    assert len(poses) >= 2
    assert poses[0].joints
    walk = engines.walking_engine("natural", bias)
    run = engines.running_engine("athletic", bias)
    assert walk["preserve_body"] is True
    assert run["preserve_body"] is True
    hands = engines.hand_gesture_engine("waving", "natural", bias)
    assert hands[0]["preserve_proportions"] is True
    head = engines.head_movement_engine("subtle", "looking_around", bias)
    eye = engines.eye_movement_engine("natural", "talking", bias)
    face = engines.facial_expression_engine("happy", "smiling")
    assert head["preserve_identity"] and eye["preserve_identity"]
    assert face["face_lock_respected"] and face["no_identity_drift"]


def test_library_and_custom_actions_unit():
    lib = library.list_motion_library()
    assert lib["action_count"] >= 21
    assert lib["extensible"] is True
    ids = {a["action_id"] for a in lib["actions"]}
    for required in ("walking", "running", "sitting", "standing", "talking", "custom"):
        assert required in ids
    library.register_action("parkour_vault", {"category": "stunt", "default_duration": 1.8})
    assert library.resolve_action("parkour_vault") == "parkour_vault"


def test_motion_generate_integration():
    char = cg_engine.create_character(
        name="Motion Lead",
        registry_slot="Character_A",
        body_type="athletic",
    )
    cid = char.character.character_id
    result = engine.generate_motion(
        character_id=cid,
        actions=["walking", "waving", "talking"],
        emotion="happy",
        duration_sec=6.0,
        director_plan={"plan_id": "dir_1"},
        camera_plan={"job_id": "cam_1"},
        audio_summary={"dialogue": True},
    )
    assert result["state"] == "completed"
    assert result["clip_count"] == 3
    assert result["consistent"] is True
    assert result["consistency"]["no_body_distortion"] is True
    assert result["integrations"]["face_lock"]["identity_preserved"] is True
    assert result["integrations"]["director_engine"]["linked"] is True
    assert result["integrations"]["camera_engine"]["linked"] is True
    assert result["observability"]["processing_time_ms"] >= 0
    fetched = engine.get_motion(result["job_id"])
    assert fetched is not None
    assert fetched["job_id"] == result["job_id"]


def test_character_consistency():
    locked = profile.build_motion_profile(
        "char_test",
        overrides={"body_shape": "athletic", "height": "tall", "walking_style": "confident"},
    )
    ok = profile.validate_body_consistency(locked)
    assert ok.consistent is True
    assert ok.no_body_distortion is True
    assert ok.score >= 80
    drifted = models.CharacterMotionProfile(
        **{**locked.to_dict(), "body_shape": "distorted", "height": "wrong"}
    )
    bad = profile.validate_body_consistency(locked, drifted)
    assert bad.consistent is False
    assert bad.no_body_distortion is False
    assert len(bad.drift_flags) >= 2


def test_queue_states_and_history():
    created = engine.create_motion_job(
        character_id="qchar",
        action="standing",
        emotion="calm",
    )
    assert created["state"] == "queued"
    assert created["queue"]["queued"] >= 1
    generated = engine.generate_motion(job_id=created["job_id"])
    assert generated["state"] == "completed"
    hist = engine.motion_history(limit=10)
    assert hist["count"] >= 1
    assert any(j["job_id"] == created["job_id"] for j in hist["jobs"])


def test_emotion_adapts_movement():
    calm = engine.generate_motion(action="walking", emotion="calm", duration_sec=2.0)
    angry = engine.generate_motion(action="walking", emotion="angry", duration_sec=2.0)
    calm_stride = calm["clips"][0]["locomotion"]["stride_scale"]
    angry_stride = angry["clips"][0]["locomotion"]["stride_scale"]
    assert angry_stride > calm_stride


def test_performance_generate_under_budget():
    t0 = time.perf_counter()
    for _ in range(5):
        engine.generate_motion(
            actions=["walking", "running", "sitting"],
            emotion="excited",
            duration_sec=3.0,
        )
    elapsed = time.perf_counter() - t0
    assert elapsed < 5.0  # 5 generates should be well under 5s in simulation


def test_paddle_still_works():
    status = cg_paddle.paddle_status()
    assert status["secrets_exposed"] is False
    assert all(isinstance(v, bool) for v in status["env_presence"].values())

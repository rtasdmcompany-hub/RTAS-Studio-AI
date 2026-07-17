"""Phase 5 Sprint 7 — AI Emotion, Expression & Performance Engine tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EI = ROOT / "app" / "services" / "emotion_intelligence"
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
    "app.services.emotion_intelligence",
    EI,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("library", "library.py"),
        ("analysis", "analysis.py"),
        ("expressions", "expressions.py"),
        ("performance", "performance.py"),
        ("validator", "validator.py"),
        ("memory", "memory.py"),
        ("timeline", "timeline.py"),
        ("bridge", "bridge.py"),
        ("store", "store.py"),
        ("queue", "queue.py"),
        ("engine", "engine.py"),
    ],
)

version = sys.modules["app.services.emotion_intelligence.version"]
library = sys.modules["app.services.emotion_intelligence.library"]
analysis = sys.modules["app.services.emotion_intelligence.analysis"]
expressions = sys.modules["app.services.emotion_intelligence.expressions"]
performance = sys.modules["app.services.emotion_intelligence.performance"]
validator = sys.modules["app.services.emotion_intelligence.validator"]
memory = sys.modules["app.services.emotion_intelligence.memory"]
store = sys.modules["app.services.emotion_intelligence.store"]
queue_mod = sys.modules["app.services.emotion_intelligence.queue"]
engine = sys.modules["app.services.emotion_intelligence.engine"]
cg_paddle = sys.modules["app.services.character_generation.paddle_status"]


def setup_function():
    store.clear()
    queue_mod.emotion_queue.clear()
    memory.clear()


def test_version_unit():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 5
    assert version.SPRINT == 7


def test_emotion_library_unit():
    lib = library.list_emotion_library()
    assert lib["emotion_count"] >= 20
    assert lib["extensible"] is True
    ids = {e["emotion_id"] for e in lib["emotions"]}
    for required in ("happy", "sad", "angry", "romantic", "fear", "thinking", "surprised"):
        assert required in ids
    library.register_emotion("bittersweet", {"valence": 0.1, "arousal": 0.4})
    assert library.resolve_emotion("bittersweet") == "bittersweet"


def test_expression_generation_unit():
    expr = expressions.generate_facial_expression("happy", intensity=0.8)
    assert expr.face_lock_respected is True
    assert expr.smile_intensity > 0.4
    assert "eye_movement" in expr.to_dict()
    assert expr.blink_timing["rate_hz"] > 0
    angry = expressions.generate_facial_expression("angry")
    assert angry.mouth_expression["shape"] in ("tight", "open", "neutral", "downturned", "wide_open_smile")
    v = validator.validate_expression(expr)
    assert v["ok"] is True
    assert v["expression_score"] >= 75


def test_scene_emotion_analysis_unit():
    result = analysis.analyze_scene(
        "The hero feels fear in the dark alley. Suddenly danger approaches.",
        dialogue="I am afraid of what waits behind you!",
    )
    assert result.scene_emotion in ("fear", "suspense")
    assert result.performance_intensity > 0
    assert len(result.recommendations) >= 2


def test_generate_integration_and_consistency():
    result = engine.generate_emotion(
        prompt="She is smiling with joy and laughing with friends.",
        character_id="char_emo_1",
        emotion_hint="happy",
        director_plan={"plan_id": "dir1"},
        motion_plan={"job_id": "mot1"},
        camera_plan={"job_id": "cam1"},
        voice_plan={"emotion": "happy"},
    )
    assert result["state"] == "completed"
    assert result["expression"]["face_lock_respected"] is True
    assert result["consistency"]["identity_preserved"] is True
    assert result["consistent"] is True
    assert result["performance"]["natural_breathing"]["preserve_body"] is True
    assert result["integrations"]["motion_engine"]["linked"] is True
    assert result["observability"]["expression_score"] >= 75
    fetched = engine.get_emotion(result["job_id"])
    assert fetched is not None


def test_character_consistency_and_memory():
    first = engine.generate_emotion(
        prompt="A calm moment of peace.",
        character_id="char_mem",
        emotion_hint="calm",
    )
    assert first["consistent"] is True
    assert memory.last_emotion("char_mem") == "calm"
    second = engine.generate_emotion(
        prompt="Now the character is proud of the victory.",
        character_id="char_mem",
        emotion_hint="proud",
    )
    assert second["consistency"]["identity_preserved"] is True
    hist = memory.history_for("char_mem")
    assert len(hist) >= 2


def test_performance_body_sync_unit():
    body = performance.generate_body_performance("angry", intensity=0.9)
    assert body.walking_style
    assert body.hand_gestures
    assert body.intensity >= 0.8
    calm = performance.generate_body_performance("calm")
    assert calm.intensity < body.intensity


def test_stress_and_performance_budget():
    t0 = time.perf_counter()
    emotions = ["happy", "sad", "angry", "fear", "excited", "serious", "romantic", "surprised"]
    scores = []
    for emo in emotions * 2:
        out = engine.generate_emotion(
            prompt=f"Character feels {emo} intensely in this scene.",
            emotion_hint=emo,
            duration_sec=2.0,
        )
        scores.append(out["expression"]["expression_score"])
        assert out["state"] == "completed"
    elapsed = time.perf_counter() - t0
    assert elapsed < 8.0
    avg = sum(scores) / len(scores)
    assert avg >= 80.0  # emotion accuracy proxy


def test_history_library_paddle():
    engine.generate_emotion(prompt="Motivational speech to rise and achieve.", emotion_hint="motivational")
    hist = engine.emotion_history(limit=10)
    assert hist["count"] >= 1
    lib = engine.emotion_library_payload()
    assert lib["emotion_count"] >= 20
    status = cg_paddle.paddle_status()
    assert status["secrets_exposed"] is False

"""Phase 5 Sprint 4 — AI Voice & Dialogue Intelligence Engine tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VI = ROOT / "app" / "services" / "voice_intelligence"
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
    "app.services.voice_intelligence",
    VI,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("emotions", "emotions.py"),
        ("dialogue_planner", "dialogue_planner.py"),
        ("timing", "timing.py"),
        ("voice_manager", "voice_manager.py"),
        ("narration", "narration.py"),
        ("consistency", "consistency.py"),
        ("store", "store.py"),
        ("engine", "engine.py"),
    ],
)

version = sys.modules["app.services.voice_intelligence.version"]
models = sys.modules["app.services.voice_intelligence.models"]
store = sys.modules["app.services.voice_intelligence.store"]
engine = sys.modules["app.services.voice_intelligence.engine"]
emotions = sys.modules["app.services.voice_intelligence.emotions"]
planner = sys.modules["app.services.voice_intelligence.dialogue_planner"]
timing = sys.modules["app.services.voice_intelligence.timing"]
narration = sys.modules["app.services.voice_intelligence.narration"]
cg_paddle = sys.modules["app.services.character_generation.paddle_status"]

SAMPLE_SCRIPT = """
Narrator: In a quiet city, hope begins to rise.
Character A: I believe we can achieve this dream together!
Character B: This is a critical decision. We must stay serious.
Character C: I love you more than forever.
Internal: What if danger is waiting behind you?
Voice-over: Stay calm and breathe.
Group: Yes! Let's go!
"""


def setup_function():
    store.clear()


def test_version():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 5
    assert version.SPRINT == 4


def test_emotion_detection():
    assert emotions.detect_emotion("I am so happy and full of joy") == "happy"
    assert emotions.detect_emotion("I feel sad and heartbroken") == "sad"
    assert emotions.detect_emotion("I am furious with rage") == "angry"
    assert emotions.detect_emotion("I love you forever darling") == "romantic"
    assert emotions.detect_emotion("Believe and achieve your dream") == "motivational"
    assert emotions.detect_emotion("I am afraid of the danger") == "fear"
    assert emotions.detect_emotion("This is a critical decision") == "serious"
    assert emotions.detect_emotion("Stay calm and breathe softly") == "calm"
    assert emotions.detect_emotion("Suddenly who is behind you") == "suspense"
    assert emotions.detect_emotion("Wow this is amazing!") == "excited"


def test_dialogue_planning():
    lines = planner.plan_dialogue(SAMPLE_SCRIPT, project_id="p1")
    roles = {ln.role for ln in lines}
    assert "narrator" in roles
    assert "character_a" in roles
    assert "character_b" in roles
    assert "character_c" in roles
    assert "internal_thought" in roles
    assert "voice_over" in roles
    assert "group" in roles
    summary = planner.dialogue_role_summary(lines)
    assert summary["has_narrator"]
    assert summary["has_characters"]
    assert summary["line_count"] >= 7


def test_voice_assignment():
    result = engine.analyze_script(SAMPLE_SCRIPT, project_id="assign_proj", language="en")
    profiles = result["voice_profiles"]
    assert "character_a" in profiles
    assert "narrator" in profiles
    for role, profile in profiles.items():
        for field in models.VOICE_PROFILE_FIELDS:
            assert field in profile
        assert profile["voice_id"]
    # Same role keeps same voice across lines
    a_voices = {ln["voice_id"] for ln in result["lines"] if ln["role"] == "character_a"}
    assert len(a_voices) == 1

    reassigned = engine.assign_project_voices(
        "assign_proj",
        assignments=[{"role": "character_a", "voice_id": "rtas_en_female_custom01", "accent": "british"}],
    )
    assert reassigned["voice_profiles"]["character_a"]["voice_id"] == "rtas_en_female_custom01"
    assert reassigned["voice_profiles"]["character_a"]["accent"] == "british"


def test_timing_calculation():
    result = engine.analyze_script(SAMPLE_SCRIPT, project_id="timing_proj")
    timing_plan = result["timing"]
    assert timing_plan["total_duration_sec"] > 0
    assert timing_plan["speaking_duration_sec"] > 0
    assert timing_plan["overlap_prevented"] is True
    assert "transition_timing_sec" in timing_plan
    # Sequential lines
    lines = result["lines"]
    for i in range(1, len(lines)):
        assert lines[i]["start_sec"] >= lines[i - 1]["end_sec"] - 0.001


def test_narration_generation():
    result = engine.analyze_script(SAMPLE_SCRIPT, project_id="narr_proj")
    narr = result["narration_summary"]
    assert narr["narration_generated"] is True
    assert narr["narrator"]["count"] >= 1
    assert narr["voice_over"]["count"] >= 1
    assert narr["internal_thoughts"]["count"] >= 1
    assert "recommended_mix" in narr


def test_consistency_verification():
    result = engine.analyze_script(SAMPLE_SCRIPT, project_id="cons_proj")
    synced = engine.synchronize_project("cons_proj")
    assert synced["synchronized"] is True
    cons = synced["consistency"]
    assert cons["same_voice_across_scenes"] is True
    assert cons["dialogue_synchronized"] is True
    assert cons["no_unexpected_switching"] is True
    assert cons["consistency_score"] >= 75
    assert cons["consistent"] is True

    fetched = engine.get_project("cons_proj")
    assert fetched is not None
    assert fetched["project_id"] == "cons_proj"


def test_paddle_still_works():
    status = cg_paddle.paddle_status()
    assert status["secrets_exposed"] is False
    assert "env_presence" in status
    assert all(isinstance(v, bool) for v in status["env_presence"].values())

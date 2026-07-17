"""Phase 4 Sprint 1 — AI Audio Production Engine tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AE = ROOT / "app" / "services" / "audio_engine"


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


def _load_pkg(pkg_name: str, pkg_path: Path, modules: list[tuple[str, str]]):
    _ensure_parents(pkg_name)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    pkg = type(sys)(pkg_name)
    pkg.__path__ = [str(pkg_path)]
    sys.modules[pkg_name] = pkg
    for mod_name, file_name in modules:
        _load(f"{pkg_name}.{mod_name}", pkg_path / file_name)


_load_pkg(
    "app.services.audio_engine",
    AE,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("store", "store.py"),
        ("queue", "queue.py"),
        ("voice", "voice.py"),
        ("music", "music.py"),
        ("ambient", "ambient.py"),
        ("sfx", "sfx.py"),
        ("timeline", "timeline.py"),
        ("metadata", "metadata.py"),
        ("validator", "validator.py"),
        ("exporter", "exporter.py"),
        ("observability", "observability.py"),
        ("engine", "engine.py"),
    ],
)

engine = sys.modules["app.services.audio_engine.engine"]
version = sys.modules["app.services.audio_engine.version"]
queue_mod = sys.modules["app.services.audio_engine.queue"]
validator = sys.modules["app.services.audio_engine.validator"]
voice = sys.modules["app.services.audio_engine.voice"]


def test_version_stamp():
    assert version.ENGINE_VERSION == "0.1.0"
    assert "Audio Production" in version.ENGINE_NAME


def test_validation_unit():
    clips = voice.build_voice_clips("Hello world from Karachi")
    result = validator.validate_audio_plan(
        prompt="Hello world from Karachi",
        voice=clips,
        music=[],
        ambient=[],
        sfx=[],
        duration_sec=3.0,
    )
    assert result.passed is True
    assert clips


def test_full_plan_and_store():
    director = {
        "voice_timeline": [
            {
                "text": "Welcome to RTAS Studio",
                "character": "Narrator",
                "start_sec": 0,
                "end_sec": 3,
                "language": "en",
            }
        ],
        "music_timeline": [
            {"style": "cinematic", "mood": "warm", "start_sec": 0, "end_sec": 8}
        ],
        "ambient_timeline": [
            {"label": "soft room tone", "start_sec": 0, "end_sec": 8, "intensity": 0.4}
        ],
        "sfx_timeline": [
            {"label": "whoosh", "category": "transition", "start_sec": 2.5, "duration_sec": 0.4}
        ],
    }
    plan = engine.build_audio_engine_plan(
        "Cinematic welcome voiceover",
        audio_director=director,
        enqueue=True,
        auto_process=True,
        parent_generation_id="gen_test_1",
    )
    assert plan.job_id.startswith("audioeng_")
    assert plan.version == "0.1.0"
    assert len(plan.voice_clips) >= 1
    assert len(plan.music_clips) >= 1
    assert len(plan.timeline) == 4
    assert plan.validation.passed is True
    assert plan.state == "completed"
    assert plan.production_ready is True
    assert plan.export.ready is True
    assert engine.get_plan(plan.job_id) is not None
    summary = plan.summary()
    assert summary["voice_clips"] >= 1
    assert summary["validation_passed"] is True


def test_queue_retry_cancel():
    q = queue_mod.audio_queue
    q.clear()
    plan = engine.build_audio_engine_plan(
        "Queue stress line",
        enqueue=True,
        auto_process=False,
        parent_generation_id="gen_q",
    )
    assert plan.state == "queued"
    assert plan.queue_position is not None
    status = q.status()
    assert status["queued"] >= 1

    processed = engine.process_audio_job(plan.job_id)
    assert processed is not None
    assert processed.state in ("completed", "failed")

    # Force fail path then retry
    processed.state = "failed"
    q.update_state(processed.job_id, "failed", error="forced")
    retried = q.retry(processed.job_id)
    assert retried is not None
    assert retried.state == "retrying"
    assert retried.retry_count >= 1
    again = engine.process_audio_job(processed.job_id)
    assert again is not None

    cancelled_src = engine.build_audio_engine_plan(
        "Cancel me",
        enqueue=True,
        auto_process=False,
    )
    cancelled = q.cancel(cancelled_src.job_id)
    assert cancelled is not None
    assert cancelled.state == "cancelled"


def test_dict_shape():
    result = engine.build_audio_engine_dict(
        "Dict shape check with rain ambience and footsteps"
    )
    assert result["version"] == "0.1.0"
    assert "plan" in result and "summary" in result
    assert result["summary"]["job_id"].startswith("audioeng_")


if __name__ == "__main__":
    test_version_stamp()
    test_validation_unit()
    test_full_plan_and_store()
    test_queue_retry_cancel()
    test_dict_shape()
    print("OK audio_engine")

"""Phase 4 Sprint 4 — Music Generation & Composition Engine tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MG = ROOT / "app" / "services" / "music_generation"


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
    "app.services.music_generation",
    MG,
    [
        ("version", "version.py"),
        ("genres", "genres.py"),
        ("instruments", "instruments.py"),
        ("models", "models.py"),
        ("validation", "validation.py"),
        ("observability", "observability.py"),
        ("cache", "cache.py"),
        ("store", "store.py"),
        ("queue", "queue.py"),
        ("video_bridge", "video_bridge.py"),
        ("library", "library.py"),
        ("engine", "engine.py"),
    ],
)

version = sys.modules["app.services.music_generation.version"]
genres = sys.modules["app.services.music_generation.genres"]
instruments = sys.modules["app.services.music_generation.instruments"]
validation = sys.modules["app.services.music_generation.validation"]
store = sys.modules["app.services.music_generation.store"]
queue_mod = sys.modules["app.services.music_generation.queue"]
video_bridge = sys.modules["app.services.music_generation.video_bridge"]
library = sys.modules["app.services.music_generation.library"]
engine = sys.modules["app.services.music_generation.engine"]


def setup_function():
    store.clear()
    queue_mod.music_queue.clear()


def test_version():
    assert version.ENGINE_VERSION == "1.0.0"
    assert "Music Generation" in version.ENGINE_NAME
    assert version.SPRINT == 4


def test_genres_pluggable():
    codes = {g["code"] for g in genres.list_genres()}
    required = {
        "cinematic", "epic", "emotional", "sad", "romantic", "corporate",
        "documentary", "action", "horror", "sci-fi", "hip-hop", "lo-fi",
        "orchestral", "electronic", "ambient", "acoustic",
    }
    assert required <= codes
    genres.register_genre(
        genres.GenreDef("jazz", "Jazz", 110, "cool", 0.5, "Bb", ("swing",))
    )
    assert genres.normalize_genre("jazz") == "jazz"


def test_instruments():
    codes = {i["code"] for i in instruments.list_instruments()}
    assert "piano" in codes and "strings" in codes
    resolved = instruments.resolve_instruments(None, "epic")
    assert "brass" in resolved


def test_validation():
    bad = validation.validate_generate_request(genre="zzz", bpm=10, duration_sec=0.5)
    assert not bad.ok
    good = validation.validate_generate_request(
        genre="cinematic", role="background", bpm=90, duration_sec=30, energy=0.6
    )
    assert good.ok
    assert good.instruments


def test_video_adaptation():
    adapted = video_bridge.adapt_from_video_context(
        prompt="intense action chase",
        scenes=[{"emotion": "action", "duration_sec": 18, "beat": "climax"}],
        camera_motion="whip pan",
        character_memory=[{"emotion_profile": "confident"}],
    )
    assert adapted["genre"] == "action"
    assert adapted["duration_sec"] == 18.0
    assert adapted["energy"] >= 0.7


def test_generate_and_library():
    setup_function()
    job = engine.generate_music(
        genre="cinematic",
        role="theme",
        bpm=92,
        duration_sec=24,
        instruments=["piano", "strings"],
        loop=True,
        fade_in_sec=1.5,
        fade_out_sec=2.0,
    )
    assert job.job_id.startswith("musicjob_")
    assert job.state == "completed"
    assert job.production_ready
    assert job.library_id
    assert job.controls.stems
    assert job.stem_urls
    assert job.metadata["provider_secret_exposed"] is False
    lib = library.library_payload(genre="cinematic")
    assert lib["count"] >= 1
    assert any(i["job_id"] == job.job_id for i in lib["items"])


def test_queue_retry_cancel():
    setup_function()
    job = engine.generate_music(
        genre="ambient",
        duration_sec=10,
        enqueue=True,
        auto_process=False,
    )
    assert job.state == "queued"
    processed = engine.process_music_job(job.job_id)
    assert processed and processed.state == "completed"
    # Walked composing/generating/mixing via history
    states = [h["state"] for h in processed.history]
    assert "composing" in states
    assert "mixing" in states

    queue_mod.music_queue.update_state(job.job_id, "failed", error="boom")
    retried = queue_mod.music_queue.retry(job.job_id)
    assert retried and retried.state == "retrying"
    again = engine.process_music_job(job.job_id)
    assert again and again.state == "completed"

    job2 = engine.generate_music(genre="lo-fi", duration_sec=8, auto_process=False)
    cancelled = queue_mod.music_queue.cancel(job2.job_id)
    assert cancelled and cancelled.state == "cancelled"


def test_roles_and_versioning():
    setup_function()
    for role in ("background", "intro", "outro", "theme", "loop", "instrumental"):
        job = engine.generate_music(genre="orchestral", role=role, duration_sec=12)
        assert job.role == role
        assert job.state == "completed"
    vers = engine.version_payload()
    assert vers["version"] == "1.0.0"
    assert len(vers["job_versions"]) >= 1


def test_performance_fast_generation():
    setup_function()
    t0 = time.perf_counter()
    for i in range(5):
        engine.generate_music(genre="electronic", bpm=120 + i, duration_sec=10 + i)
    elapsed = time.perf_counter() - t0
    assert elapsed < 2.0  # simulation path must stay fast


def run_all():
    tests = [
        test_version,
        test_genres_pluggable,
        test_instruments,
        test_validation,
        test_video_adaptation,
        test_generate_and_library,
        test_queue_retry_cancel,
        test_roles_and_versioning,
        test_performance_fast_generation,
    ]
    for fn in tests:
        setup_function()
        fn()
    print("OK music_generation")


if __name__ == "__main__":
    run_all()

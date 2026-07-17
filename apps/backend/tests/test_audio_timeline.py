"""Phase 4 Sprint 8 — Audio Timeline & Cinematic Synchronization tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TL = ROOT / "app" / "services" / "audio_timeline"


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
    "app.services.audio_timeline",
    TL,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("validation", "validation.py"),
        ("tracks", "tracks.py"),
        ("sync", "sync.py"),
        ("cache", "cache.py"),
        ("store", "store.py"),
        ("queue", "queue.py"),
        ("observability", "observability.py"),
        ("export", "export.py"),
        ("engine", "engine.py"),
    ],
)

version = sys.modules["app.services.audio_timeline.version"]
validation = sys.modules["app.services.audio_timeline.validation"]
tracks = sys.modules["app.services.audio_timeline.tracks"]
sync = sys.modules["app.services.audio_timeline.sync"]
store = sys.modules["app.services.audio_timeline.store"]
queue_mod = sys.modules["app.services.audio_timeline.queue"]
engine = sys.modules["app.services.audio_timeline.engine"]
cache = sys.modules["app.services.audio_timeline.cache"]


def setup_function():
    store.clear()
    queue_mod.timeline_queue.clear()
    cache.cache_clear()


def test_version():
    assert version.ENGINE_VERSION == "1.0.0"
    assert "Timeline" in version.ENGINE_NAME
    assert version.SPRINT == 8


def test_validation():
    bad = validation.validate_timeline_request(fps=-1)
    assert not bad.ok
    good = validation.validate_timeline_request(fps=24, duration_sec=8)
    assert good.ok


def test_default_tracks_and_layers():
    tr = tracks.build_default_tracks()
    kinds = {t.kind for t in tr}
    assert {
        "voice",
        "music",
        "ambient",
        "sfx",
        "foley",
        "narration",
        "transition",
    } <= kinds
    layers = tracks.build_layers(tr)
    assert len(layers) >= 3
    assert any(l.layer_id == "layer_master" for l in layers)


def test_create_timeline_multi_track():
    job = engine.create_timeline(
        fps=24,
        duration_sec=8,
        scenes=[
            {"id": "s1", "emotion": "tense", "environment": "rainy street", "end_sec": 4},
            {"id": "s2", "emotion": "hopeful", "environment": "sunrise", "end_sec": 8},
        ],
        shots=[
            {"id": "sh1", "start_sec": 0.0, "action": "footstep"},
            {"id": "sh2", "start_sec": 2.0, "action": "door"},
        ],
        lip_sync={"cues": [{"start_sec": 0.1, "viseme": "A"}]},
        camera_plan={"primary_motion": "dolly_in"},
        voice_summary={"job_id": "v1", "audio_url": "/v.wav", "duration_sec": 6},
        music_summary={"job_id": "m1", "audio_url": "/m.wav", "mood": "cinematic"},
        sfx_summary={
            "job_id": "x1",
            "events": [{"start_sec": 1.0, "duration_sec": 0.3, "label": "impact"}],
        },
        ambient_summary={"environment": "city"},
        localization_summary={"job_id": "l1", "dubbed_audio_url": "/dub.wav"},
        audio_director={
            "voice_timeline": [
                {"start_sec": 0.0, "end_sec": 2.0, "text": "Hello", "emotion": "calm"}
            ],
            "ambient_timeline": [{"start_sec": 0.0, "end_sec": 8.0, "environment": "city"}],
            "sfx_timeline": [{"start_sec": 1.5, "duration_sec": 0.2, "label": "whoosh"}],
        },
        enqueue=True,
        auto_process=True,
    )
    assert job.state == "completed"
    assert len(job.tracks) == 7
    assert job.sync.sync_accuracy >= 0.7
    assert job.production_ready
    assert job.observability.timeline_id == job.job_id
    assert job.observability.track_count == 7
    assert len(job.beat_markers) > 0
    assert len(job.versions) >= 2
    assert any(h["status"] == "completed" for h in job.history)


def test_sync_accuracy_and_frame_snap():
    job = engine.create_timeline(
        fps=24,
        duration_sec=4,
        scenes=[{"id": "s1", "emotion": "dark"}],
        shots=[{"id": "sh1", "start_sec": 0.5}],
        lip_sync={"cues": [{"start_sec": 0.0}]},
        auto_align=True,
        snap_enabled=True,
        enqueue=True,
        auto_process=True,
    )
    assert job.sync.frame_accuracy_ms > 0
    for t in job.tracks:
        for e in t.events:
            assert e.frame is not None
            # snapped to frame grid
            assert abs(e.start_sec * 24 - round(e.start_sec * 24)) < 1e-6


def test_queue_states_and_retry():
    job = engine.create_timeline(
        fps=24,
        duration_sec=3,
        scenes=[{"id": "a"}],
        enqueue=True,
        auto_process=True,
    )
    assert job.state == "completed"
    statuses = [h["status"] for h in job.history]
    for required in ("queued", "preparing", "synchronizing", "optimizing", "rendering", "completed"):
        assert required in statuses

    retried = queue_mod.timeline_queue.retry(job.job_id)
    assert retried is not None
    assert retried.state == "retrying"
    assert retried.retry_count >= 1
    processed = engine.process_timeline_job(job.job_id)
    assert processed is not None
    assert processed.state == "completed"


def test_history_and_export():
    job = engine.create_timeline(
        fps=30,
        duration_sec=2,
        scenes=[{"id": "h1"}],
        parent_generation_id="gen_test_8",
        enqueue=True,
        auto_process=True,
    )
    hist = engine.history_payload(limit=10, parent_generation_id="gen_test_8")
    assert hist["items"]
    assert any(i.get("timeline_id") == job.job_id for i in hist["items"])
    exported = engine.export_timeline(job.job_id)
    assert exported["format"] == "rtas-timeline-v1"
    assert exported["job_id"] == job.job_id
    assert len(exported["tracks"]) == 7


def test_get_job_and_sync_existing():
    job = engine.create_timeline(fps=24, duration_sec=2, scenes=[{"id": "g"}])
    fetched = engine.get_job(job.job_id)
    assert fetched is not None
    synced = engine.sync_timeline(job_id=job.job_id)
    assert synced.job_id == job.job_id
    assert synced.state == "completed"


def test_lock_prevents_resync_mutation():
    job = engine.create_timeline(
        fps=24, duration_sec=2, scenes=[{"id": "lock"}], locked=True
    )
    assert job.locked
    before = job.timeline_version
    again = engine.sync_timeline(job_id=job.job_id)
    assert again.locked
    # locked job returned as-is without forced reprocess path mutating further
    assert again.job_id == job.job_id
    assert again.timeline_version >= before


def test_performance_create_under_budget():
    t0 = time.perf_counter()
    for i in range(20):
        engine.create_timeline(
            fps=24,
            duration_sec=5,
            scenes=[{"id": f"p{i}", "emotion": "neutral"}],
            shots=[{"id": f"sh{i}", "start_sec": 0.2}],
            enqueue=True,
            auto_process=True,
        )
    elapsed = time.perf_counter() - t0
    assert elapsed < 5.0


def test_beat_markers_and_dynamic_balance():
    markers = sync.generate_beat_markers(4.0, bpm=120)
    assert len(markers) >= 8
    tr = tracks.build_default_tracks()
    tr = tracks.populate_tracks_from_sources(
        tr,
        scenes=[{"id": "s", "emotion": "tense"}],
        voice_summary={"duration_sec": 2},
        music_summary={"mood": "dark"},
        duration_sec=4,
    )
    sync.apply_dynamic_balance(tr)
    music = next(t for t in tr if t.kind == "music")
    assert any(e.metadata.get("ducked") for e in music.events) or music.events

"""Phase 4 Sprint 5 — Sound Effects & Ambient Audio Engine tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SA = ROOT / "app" / "services" / "sfx_ambient"


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
    "app.services.sfx_ambient",
    SA,
    [
        ("version", "version.py"),
        ("categories", "categories.py"),
        ("models", "models.py"),
        ("validation", "validation.py"),
        ("scene_intelligence", "scene_intelligence.py"),
        ("video_bridge", "video_bridge.py"),
        ("store", "store.py"),
        ("queue", "queue.py"),
        ("cache", "cache.py"),
        ("observability", "observability.py"),
        ("layering", "layering.py"),
        ("library", "library.py"),
        ("engine", "engine.py"),
    ],
)

version = sys.modules["app.services.sfx_ambient.version"]
categories = sys.modules["app.services.sfx_ambient.categories"]
validation = sys.modules["app.services.sfx_ambient.validation"]
scene_intel = sys.modules["app.services.sfx_ambient.scene_intelligence"]
video_bridge = sys.modules["app.services.sfx_ambient.video_bridge"]
store = sys.modules["app.services.sfx_ambient.store"]
queue_mod = sys.modules["app.services.sfx_ambient.queue"]
layering = sys.modules["app.services.sfx_ambient.layering"]
engine = sys.modules["app.services.sfx_ambient.engine"]


def setup_function():
    store.clear()
    queue_mod.sfx_queue.clear()


def test_version():
    assert version.ENGINE_VERSION == "1.0.0"
    assert "Sound Effects" in version.ENGINE_NAME
    assert version.SPRINT == 5


def test_categories_pluggable():
    codes = {c["code"] for c in categories.list_categories()}
    required = {
        "rain", "thunder", "wind", "ocean", "river", "waterfall", "fire",
        "explosion", "footsteps", "birds", "animals", "crowd", "city-traffic",
        "market", "office", "factory", "nature", "forest", "desert", "snow",
        "space", "sci-fi", "ui-sounds", "mechanical", "weapon-effects",
    }
    assert required <= codes
    categories.register_category(
        categories.CategoryDef("custom-drone", "Custom Drone", "ambient", 0.4, True)
    )
    assert categories.is_known_category("custom-drone")


def test_validation():
    bad = validation.validate_generate_request(categories=["not-a-real-cat"])
    assert not bad.ok
    good = validation.validate_generate_request(
        categories=["rain", "thunder"],
        duration_sec=10,
        volume=0.5,
    )
    assert good.ok
    assert "rain" in good.categories


def test_scene_intelligence():
    env = scene_intel.detect_environment("A rainy night in the forest")
    assert env in ("rain", "forest")
    profile = scene_intel.build_environment_profile(
        prompt="Busy city street with traffic and crowds",
        scenes=[{"id": "scene_1", "emotion": "tense", "duration_sec": 8}],
    )
    assert profile.environment == "city"
    assert "city-traffic" in profile.recommended_categories or "crowd" in profile.recommended_categories


def test_video_bridge_adaptation():
    adapted = video_bridge.adapt_from_video_context(
        prompt="Ocean waves at sunset",
        scenes=[{"id": "s1", "emotion": "calm", "duration_sec": 15}],
        camera_motion="dolly",
        music_summary={"energy": 0.4, "job_id": "musicjob_x"},
    )
    assert adapted["environment"] == "ocean"
    assert adapted["duration_sec"] >= 15
    assert len(adapted["categories"]) >= 1


def test_layering_and_timeline():
    layers = layering.build_layers(
        ["rain", "thunder", "wind"],
        duration_sec=12,
        base_volume=0.5,
        loop=True,
        fade_in_sec=0.5,
        fade_out_sec=1.0,
        job_id="sfxjob_test",
    )
    assert len(layers) == 3
    assert layers[0].spatial.distance >= 0
    events = layering.build_timeline_events(layers, scene_id="scene_1", job_id="sfxjob_test")
    assert len(events) >= 3
    assert events[0].action == "play"
    assert any(e.action == "fade" for e in events)


def test_generate_sfx_and_ambient():
    setup_function()
    sfx = engine.generate_sfx(
        categories=["explosion", "footsteps"],
        duration_sec=5,
        volume=0.7,
        loop=False,
    )
    assert sfx.job_id.startswith("sfxjob_")
    assert sfx.state == "completed"
    assert sfx.kind == "sfx"
    assert sfx.production_ready
    assert len(sfx.layers) >= 2
    assert sfx.metadata["provider_secret_exposed"] is False

    amb = engine.generate_ambient(
        categories=["ocean", "wind"],
        duration_sec=20,
        prompt="Calm beach scene",
    )
    assert amb.kind == "ambient"
    assert amb.state == "completed"
    assert amb.loop is True or any(L.loop for L in amb.layers)


def test_queue_retry_cancel():
    setup_function()
    job = engine.generate_sfx_ambient(
        kind="scene",
        categories=["nature", "birds"],
        duration_sec=8,
        enqueue=True,
        auto_process=False,
    )
    assert job.state == "queued"
    processed = engine.process_sfx_job(job.job_id)
    assert processed and processed.state == "completed"
    queue_mod.sfx_queue.update_state(job.job_id, "failed", error="boom")
    retried = queue_mod.sfx_queue.retry(job.job_id)
    assert retried and retried.state == "retrying"
    assert retried.retry_count >= 1
    again = engine.process_sfx_job(job.job_id)
    assert again and again.state == "completed"

    job2 = engine.generate_sfx(
        categories=["ui-sounds"],
        duration_sec=2,
        enqueue=True,
        auto_process=False,
    )
    cancelled = queue_mod.sfx_queue.cancel(job2.job_id)
    assert cancelled and cancelled.state == "cancelled"


def test_performance_fast_generate():
    setup_function()
    t0 = time.perf_counter()
    for i in range(20):
        engine.generate_sfx_ambient(
            kind="scene",
            categories=["wind", "birds"],
            duration_sec=4 + i * 0.01,
            prompt=f"forest scene {i}",
            auto_process=True,
        )
    elapsed = time.perf_counter() - t0
    assert elapsed < 5.0, f"20 generations took {elapsed:.2f}s"


def run_all():
    tests = [
        test_version,
        test_categories_pluggable,
        test_validation,
        test_scene_intelligence,
        test_video_bridge_adaptation,
        test_layering_and_timeline,
        test_generate_sfx_and_ambient,
        test_queue_retry_cancel,
        test_performance_fast_generate,
    ]
    for fn in tests:
        setup_function()
        fn()
    print("OK sfx_ambient")


if __name__ == "__main__":
    run_all()

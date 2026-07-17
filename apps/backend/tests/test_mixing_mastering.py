"""Phase 4 Sprint 6 — Mixing & Mastering Engine tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MM = ROOT / "app" / "services" / "mixing_mastering"


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
    "app.services.mixing_mastering",
    MM,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("validation", "validation.py"),
        ("quality", "quality.py"),
        ("mixing", "mixing.py"),
        ("mastering", "mastering.py"),
        ("store", "store.py"),
        ("queue", "queue.py"),
        ("cache", "cache.py"),
        ("observability", "observability.py"),
        ("bridge", "bridge.py"),
        ("engine", "engine.py"),
    ],
)

version = sys.modules["app.services.mixing_mastering.version"]
validation = sys.modules["app.services.mixing_mastering.validation"]
quality = sys.modules["app.services.mixing_mastering.quality"]
mixing = sys.modules["app.services.mixing_mastering.mixing"]
store = sys.modules["app.services.mixing_mastering.store"]
queue_mod = sys.modules["app.services.mixing_mastering.queue"]
engine = sys.modules["app.services.mixing_mastering.engine"]


def setup_function():
    store.clear()
    queue_mod.mix_queue.clear()


def test_version():
    assert version.ENGINE_VERSION == "1.0.0"
    assert "Mixing" in version.ENGINE_NAME
    assert version.SPRINT == 6


def test_validation():
    bad = validation.validate_mix_master_request(target_lufs=0)
    assert not bad.ok
    good = validation.validate_mix_master_request(
        target_lufs=-14, export_format="wav", sample_rate=48000, bit_depth=24
    )
    assert good.ok


def test_quality_analysis():
    loud = quality.analyze_loudness(job_id="mixjob_q1", pre_normalized=True)
    assert -16 <= loud.integrated_lufs <= -12
    assert loud.normalized
    freq = quality.analyze_frequency(job_id="mixjob_q1")
    assert freq.tonal_balance_score > 0
    report = quality.build_quality_report(
        loudness=loud,
        frequency=freq,
        stereo_width=1.1,
        noise_floor_db=-55,
        dynamic_range_db=8,
    )
    assert report.overall_score >= 0.7
    assert report.grade in ("A", "B", "C", "D")


def test_mix_and_master():
    setup_function()
    job = engine.run_mix_master(
        kind="mix_master",
        voice_summary={"job_id": "voicejob_1", "production_ready": True},
        music_summary={"job_id": "musicjob_1", "energy": 0.7},
        sfx_summary={"job_id": "sfxjob_1", "layers": 3, "volume": 0.4},
        target_lufs=-14,
    )
    assert job.job_id.startswith("mixjob_")
    assert job.master_job_id and job.master_job_id.startswith("masterjob_")
    assert job.state == "completed"
    assert job.production_ready
    assert job.quality.overall_score >= 0.7
    assert abs(job.loudness.integrated_lufs - (-14.0)) <= 2.0
    assert job.loudness.true_peak_dbtp <= 0.0
    assert job.metadata["provider_secret_exposed"] is False
    assert "dialogue_priority" in job.metadata["mix_chain"][1]

    by_master = engine.get_job(job.master_job_id)
    assert by_master is not None
    report = engine.get_quality_report(job.job_id)
    assert report and report["quality"]["overall_score"] >= 0.7


def test_queue_retry_cancel():
    setup_function()
    job = engine.mix_audio(
        voice_summary={"job_id": "v1"},
        enqueue=True,
        auto_process=False,
    )
    assert job.state == "queued"
    processed = engine.process_mix_job(job.job_id)
    assert processed and processed.state == "completed"
    queue_mod.mix_queue.update_state(job.job_id, "failed", error="boom")
    retried = queue_mod.mix_queue.retry(job.job_id)
    assert retried and retried.state == "retrying"
    again = engine.process_mix_job(job.job_id)
    assert again and again.state == "completed"

    job2 = engine.master_audio(enqueue=True, auto_process=False)
    cancelled = queue_mod.mix_queue.cancel(job2.job_id)
    assert cancelled and cancelled.state == "cancelled"


def test_performance_and_stress():
    setup_function()
    t0 = time.perf_counter()
    for i in range(25):
        engine.run_mix_master(
            kind="mix_master",
            music_summary={"job_id": f"m{i}", "energy": 0.5},
            sfx_summary={"job_id": f"s{i}", "layers": 2},
            auto_process=True,
        )
    elapsed = time.perf_counter() - t0
    assert elapsed < 5.0, f"25 mix/master jobs took {elapsed:.2f}s"


def run_all():
    tests = [
        test_version,
        test_validation,
        test_quality_analysis,
        test_mix_and_master,
        test_queue_retry_cancel,
        test_performance_and_stress,
    ]
    for fn in tests:
        setup_function()
        fn()
    print("OK mixing_mastering")


if __name__ == "__main__":
    run_all()

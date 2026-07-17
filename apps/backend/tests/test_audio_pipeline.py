"""Phase 4 Sprint 10 — Complete Audio Production Pipeline v1.0 tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPE = ROOT / "app" / "services" / "audio_pipeline"
SERVICES = ROOT / "app" / "services"

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
    # Keep real package search paths so live/regression imports work
    if "app" in sys.modules:
        sys.modules["app"].__path__ = [str(ROOT / "app")]
    if "app.services" in sys.modules:
        sys.modules["app.services"].__path__ = [str(SERVICES)]


def _load_pkg(pkg_name: str, pkg_path: Path, modules: list[tuple[str, str]]):
    _ensure_parents(pkg_name)
    pkg = type(sys)(pkg_name)
    pkg.__path__ = [str(pkg_path)]
    sys.modules[pkg_name] = pkg
    for mod_name, file_name in modules:
        _load(f"{pkg_name}.{mod_name}", pkg_path / file_name)
    # Re-bind package exports used by engine.__init__ style imports
    eng = sys.modules[f"{pkg_name}.engine"]
    sys.modules[pkg_name].run_pipeline = eng.run_pipeline
    sys.modules[pkg_name].run_pipeline_dict = eng.run_pipeline_dict
    sys.modules[pkg_name].finalize_from_orchestrator_fields = (
        eng.finalize_from_orchestrator_fields
    )
    sys.modules[pkg_name].get_job = eng.get_job
    sys.modules[pkg_name].health_payload = eng.health_payload
    sys.modules[pkg_name].metrics_payload = eng.metrics_payload
    sys.modules[pkg_name].stress_test = eng.stress_test
    sys.modules[pkg_name].regression_checklist = eng.regression_checklist
    sys.modules[pkg_name].release_manifest = sys.modules[
        f"{pkg_name}.version"
    ].release_manifest
    sys.modules[pkg_name].ENGINE_LABEL = sys.modules[f"{pkg_name}.version"].ENGINE_LABEL
    sys.modules[pkg_name].ENGINE_VERSION = sys.modules[
        f"{pkg_name}.version"
    ].ENGINE_VERSION
    sys.modules[pkg_name].ENGINE_NAME = sys.modules[f"{pkg_name}.version"].ENGINE_NAME
    sys.modules[pkg_name].store = sys.modules[f"{pkg_name}.store"]
    sys.modules[pkg_name].pipeline_queue = sys.modules[f"{pkg_name}.queue"].pipeline_queue


_load_pkg(
    "app.services.audio_pipeline",
    PIPE,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("quality", "quality.py"),
        ("security", "security.py"),
        ("observability", "observability.py"),
        ("store", "store.py"),
        ("queue", "queue.py"),
        ("stages", "stages.py"),
        ("engine", "engine.py"),
    ],
)

version = sys.modules["app.services.audio_pipeline.version"]
quality = sys.modules["app.services.audio_pipeline.quality"]
security = sys.modules["app.services.audio_pipeline.security"]
store = sys.modules["app.services.audio_pipeline.store"]
queue_mod = sys.modules["app.services.audio_pipeline.queue"]
engine = sys.modules["app.services.audio_pipeline.engine"]


def setup_function():
    store.clear()
    queue_mod.pipeline_queue.clear()


def test_release_v1():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.SPRINT == 10
    assert version.PHASE == 4
    assert version.RELEASE_STATUS == "Production Ready"
    assert version.RELEASE_TYPE == "Stable"
    manifest = version.release_manifest()
    assert manifest["production_ready"] is True
    assert len(manifest["pipeline_stages"]) == 15
    assert "voice_generation" in manifest["pipeline_stages"]
    assert "export" in manifest["pipeline_stages"]
    assert "download" in manifest["pipeline_stages"]


def test_quality_score():
    qc = quality.compute_quality_score(
        voice_summary={"job_id": "v1", "production_ready": True},
        music_summary={"job_id": "m1", "production_ready": True},
        sfx_summary={"job_id": "x1"},
        mix_summary={
            "lufs": -14.1,
            "dynamic_range_db": 11,
            "noise_detected": False,
            "clipping_detected": False,
        },
        localization_summary={
            "job_id": "l1",
            "subtitle_url": "/s.vtt",
            "production_ready": True,
        },
        timeline_summary={"job_id": "t1", "sync_accuracy": 0.86},
        export_summary={"production_ready": True, "verified": True},
    )
    assert qc.overall_score >= 75
    assert qc.passed is True
    assert qc.audio_synchronization >= 80


def test_security_sanitize_and_secrets():
    cleaned = security.sanitize_prompt("Hello api_key=sk-abcdefghijklmnop secret")
    assert "sk-" not in cleaned or "[REDACTED]" in cleaned
    bad = security.validate_pipeline_request(prompt="")
    assert not bad["ok"]
    good = security.validate_pipeline_request(prompt="Cinematic scene")
    assert good["ok"]
    assert security.assert_no_secrets({"ok": True, "token": "[REDACTED]"})


def test_simulation_pipeline_e2e():
    job = engine.run_pipeline(
        "A hero speaks under rain while music swells",
        platform="youtube",
        mode="simulation",
        enqueue=True,
    )
    assert job.state == "completed"
    assert job.production_ready
    assert job.quality.passed
    assert job.quality.overall_score >= 75
    assert len(job.stages) == 15
    assert all(s.status == "completed" for s in job.stages)
    assert job.download_url
    assert job.export_job_id
    assert job.version == "1.0.0"
    assert job.metadata["secret_scan"] == "passed"
    names = [s.stage for s in job.stages]
    assert names[0] == "prompt"
    assert names[-1] == "download"
    assert "timeline_synchronization" in names
    assert "quality_validation" in names


def test_live_pipeline_e2e():
    """Full live module chain — requires Phase 4 packages on PYTHONPATH."""
    job = engine.run_pipeline(
        "Live pipeline cinematic dialogue with music and effects",
        platform="tiktok",
        language="en",
        target_language="ur",
        duration_sec=6.0,
        mode="live",
        enqueue=True,
        scenes=[{"id": "s1", "emotion": "tense", "environment": "city"}],
    )
    assert job.state == "completed", job.observability.errors
    assert job.production_ready
    assert job.quality.passed
    assert job.voice_job_id
    assert job.music_job_id
    assert job.sfx_job_id
    assert job.mix_job_id
    assert job.localization_job_id
    assert job.timeline_job_id
    assert job.export_job_id
    assert job.download_url
    assert job.clone_id


def test_stress_simulation():
    result = engine.stress_test(concurrent=10, mode="simulation")
    assert result["stable"] is True
    assert result["completed"] == 10
    assert result["failed"] == 0
    assert result["avg_quality"] >= 75


def test_regression_checklist():
    result = engine.regression_checklist()
    assert result["passed"] is True
    assert result["passed_count"] == result["total"]
    assert result["checks"]["phase4_pipeline"] is True
    assert result["checks"]["phase4_export"] is True
    assert result["checks"]["phase2_video_engine"] is True


def test_metrics_and_health():
    engine.run_pipeline("metrics sample", mode="simulation")
    health = engine.health_payload()
    assert health["status"] == "healthy"
    assert health["release"]["version"] == "1.0.0"
    metrics = engine.metrics_payload()
    assert metrics["metrics"]["jobs_completed"] >= 1
    assert metrics["metrics"]["success_rate"] > 0


def test_get_job():
    job = engine.run_pipeline("get job test", mode="simulation")
    fetched = engine.get_job(job.job_id)
    assert fetched is not None
    assert fetched.job_id == job.job_id


def test_performance_budget():
    t0 = time.perf_counter()
    for i in range(12):
        engine.run_pipeline(f"perf {i}", mode="simulation", platform="youtube")
    assert (time.perf_counter() - t0) < 5.0


def test_finalize_orchestrator_fields():
    fields = {
        "rtasVoiceGeneration": '{"job_id":"v1","production_ready":true}',
        "rtasMusicGeneration": '{"job_id":"m1","production_ready":true}',
        "rtasSfxAmbient": '{"job_id":"x1"}',
        "rtasMixMaster": '{"job_id":"mix1","lufs":-14.0,"production_ready":true}',
        "rtasLocalization": '{"job_id":"l1","subtitle_url":"/s.vtt","production_ready":true}',
        "rtasAudioTimeline": '{"job_id":"t1","sync_accuracy":0.87}',
        "rtasAudioExport": '{"job_id":"e1","production_ready":true,"verified":true}',
        "rtasVoiceJobId": "v1",
        "rtasMusicJobId": "m1",
        "rtasSfxJobId": "x1",
        "rtasMixJobId": "mix1",
        "rtasLocalizationJobId": "l1",
        "rtasTimelineJobId": "t1",
        "rtasExportJobId": "e1",
        "rtasExportDownloadUrl": "/dl",
        "rtasExportReady": "true",
        "rtasExportPlatform": "youtube",
    }
    job = engine.finalize_from_orchestrator_fields(fields, parent_generation_id="gen10")
    assert job.quality.passed
    assert job.production_ready
    assert job.voice_job_id == "v1"
    assert job.export_job_id == "e1"
    assert job.metadata["release"]["version"] == "1.0.0"

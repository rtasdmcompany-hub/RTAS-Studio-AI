"""Phase 10 Sprint 2 — Production performance, stress, recovery & logging tests."""

from __future__ import annotations

import importlib.util
import inspect
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVC = ROOT / "app" / "services"
JO = SVC / "job_orchestration"
VE = SVC / "video_engine"
MR = SVC / "model_routing"

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
        sys.modules["app.services"].__path__ = [str(SVC)]


def _bootstrap():
    _ensure_parents("app.services.model_routing")
    if MR.exists() and "app.services.model_routing.engine" not in sys.modules:
        pkg = type(sys)("app.services.model_routing")
        pkg.__path__ = [str(MR)]
        sys.modules["app.services.model_routing"] = pkg
        for name in (
            "version",
            "models",
            "detection",
            "rules",
            "model_registry",
            "scoring",
            "analytics",
            "engine",
        ):
            if (MR / f"{name}.py").exists():
                _load(f"app.services.model_routing.{name}", MR / f"{name}.py")

    _ensure_parents("app.services.job_orchestration")
    pkg = type(sys)("app.services.job_orchestration")
    pkg.__path__ = [str(JO)]
    sys.modules["app.services.job_orchestration"] = pkg
    for name in (
        "version",
        "models",
        "store",
        "retry",
        "queue_manager",
        "metrics",
        "orchestrator",
    ):
        _load(f"app.services.job_orchestration.{name}", JO / f"{name}.py")

    _ensure_parents("app.services.video_engine")
    vpkg = type(sys)("app.services.video_engine")
    vpkg.__path__ = [str(VE)]
    sys.modules["app.services.video_engine"] = vpkg
    for name in (
        "version",
        "models",
        "stages",
        "quality",
        "validation",
        "performance",
        "monitoring",
        "analytics",
        "recovery",
        "stress",
        "download",
        "store",
        "engine",
    ):
        _load(f"app.services.video_engine.{name}", VE / f"{name}.py")


_bootstrap()

orch = sys.modules["app.services.job_orchestration.orchestrator"]
stages_mod = sys.modules["app.services.video_engine.stages"]
ve_engine = sys.modules["app.services.video_engine.engine"]
ve_store = sys.modules["app.services.video_engine.store"]


def setup_function():
    orch.reset_orchestrator()
    orch.set_max_concurrent(8)
    ve_store.clear()


def test_stage_timers_are_per_stage():
    stages = stages_mod.evaluate_stages(
        prompt="cinematic hero shot",
        intelligence={},
        director_plan={"cinematic_rhythm": "pulse"},
        scenes=[{"i": 0}],
        shots=[{"i": 0}],
        cameras=[{"i": 0}],
        camera_motion={},
        generation={"ok": True},
        scene_render={"video_manifest": True},
        production_render={"validation": {"passed": True}, "export_specs": {}},
        multi_gpu={},
        t2v=None,
        download_ready=True,
    )
    assert len(stages) == 9
    assert all(s.duration_ms >= 0 for s in stages)
    assert [s.name for s in stages] == list(stages_mod.PIPELINE_ORDER)


def test_stress_default_off():
    sig = inspect.signature(ve_engine.build_video_engine_plan)
    assert sig.parameters["run_stress"].default is False


def test_store_eviction_cap():
    ve_store.clear()
    # Keep this light: verify cap logic without building 1000 full plans
    original = ve_store.MAX_PLANS
    try:
        ve_store.MAX_PLANS = 5
        for i in range(12):
            ve_engine.build_video_engine_plan(f"cap prompt {i}", run_stress=False)
        assert ve_store.size() <= 5
    finally:
        ve_store.MAX_PLANS = original
        ve_store.clear()


def _run_job_batch(n: int) -> dict:
    orch.reset_orchestrator()
    orch.set_max_concurrent(16)
    latencies: list[float] = []
    failures = 0
    recovered = 0
    tracemalloc.start()
    start = time.perf_counter()
    job_ids: list[str] = []
    for i in range(n):
        t0 = time.perf_counter()
        created = orch.create_job(
            prompt=f"perf job {i}",
            priority="normal",
            metadata={"work_ms": 1},
        )
        job_ids.append(created["job_id"])
        latencies.append((time.perf_counter() - t0) * 1000)
    for jid in job_ids:
        job = orch.wait_for_job(jid, timeout_sec=15.0)
        assert job is not None
        if job.state == "failed":
            failures += 1
            if job.metadata.get("recovery_available"):
                recovered += 1
        elif job.retry_count > 0 and job.state == "completed":
            recovered += 1
    elapsed = time.perf_counter() - start
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "jobs": n,
        "elapsedSec": elapsed,
        "avgLatencyMs": sum(latencies) / len(latencies) if latencies else 0,
        "peakLatencyMs": max(latencies) if latencies else 0,
        "failureCount": failures,
        "recoverySuccess": recovered,
        "memoryPeakKb": round(peak / 1024, 1),
    }


def test_stress_50_jobs():
    r = _run_job_batch(50)
    assert r["failureCount"] == 0
    assert r["elapsedSec"] < 25


def test_stress_100_jobs():
    r = _run_job_batch(100)
    assert r["failureCount"] == 0
    assert r["elapsedSec"] < 40


def test_stress_250_jobs():
    r = _run_job_batch(250)
    assert r["failureCount"] == 0
    assert r["elapsedSec"] < 75


def test_stress_500_jobs():
    r = _run_job_batch(500)
    assert r["failureCount"] == 0
    assert r["elapsedSec"] < 120
    assert r["avgLatencyMs"] < 100


def test_retry_recovery():
    orch.reset_orchestrator()
    created = orch.create_job(
        prompt="force fail once then succeed",
        metadata={"force_fail_once": True, "work_ms": 1},
        max_retries=2,
    )
    job = orch.wait_for_job(created["job_id"], timeout_sec=10.0)
    assert job is not None
    assert job.state == "completed"
    assert job.retry_count >= 1


def test_logging_has_no_secret_fields_in_perf_message():
    src = inspect.getsource(ve_engine.build_video_engine_plan)
    assert "video_engine_perf" in src
    assert "FAL_KEY" not in src
    assert "password" not in src.lower()
    assert "api_key" not in src.lower()


def test_pipeline_bottleneck_reportable():
    plan = ve_engine.build_video_engine_plan(
        "A woman walks through neon rain",
        director_plan={"cinematic_rhythm": "rising"},
        scenes=[{"i": 0}],
        shots=[{"i": 0}],
        cameras=[{"i": 0}],
        text_to_video={"ok": True},
        scene_render={"video_manifest": True},
        production_render={"validation": {"passed": True}, "export_specs": {}},
        run_stress=False,
    )
    assert plan.performance.stage_ms
    assert plan.performance.total_ms >= 0
    assert set(plan.performance.stage_ms.keys()) == set(stages_mod.PIPELINE_ORDER)


def test_migration_indexes_present():
    mig = (
        ROOT.parent
        / "web"
        / "prisma"
        / "migrations"
        / "20260719_phase10_performance_indexes"
        / "migration.sql"
    )
    assert mig.exists()
    text = mig.read_text(encoding="utf-8")
    assert "GenerationJob_backendJobId_idx" in text
    assert "GenerationJob_status_createdAt_idx" in text


def test_gzip_middleware_wired():
    main_path = ROOT / "main.py"
    text = main_path.read_text(encoding="utf-8")
    assert "GZipMiddleware" in text
    assert "minimum_size=500" in text

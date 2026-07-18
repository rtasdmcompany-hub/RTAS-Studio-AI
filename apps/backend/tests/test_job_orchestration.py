"""Phase 6 Sprint 4 — AI Job Orchestration Engine tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JO = ROOT / "app" / "services" / "job_orchestration"
MR = ROOT / "app" / "services" / "model_routing"

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


def _load_model_routing_stub():
    """Lightweight stub so orchestrator route lookup can soft-fail or work."""
    _ensure_parents("app.services.model_routing")
    if "app.services.model_routing.engine" in sys.modules:
        return
    # Load minimal routing if present
    if (MR / "engine.py").exists():
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


def _load_pkg():
    _ensure_parents("app.services.job_orchestration")
    if "app.services.job_orchestration.orchestrator" in sys.modules:
        # still reload orchestrator if needed — skip if complete
        return
    pkg = type(sys)("app.services.job_orchestration")
    pkg.__path__ = [str(JO)]
    sys.modules["app.services.job_orchestration"] = pkg
    for name in ("version", "models", "store", "retry", "queue_manager", "metrics", "orchestrator"):
        _load(f"app.services.job_orchestration.{name}", JO / f"{name}.py")


_load_model_routing_stub()
_load_pkg()

version = sys.modules["app.services.job_orchestration.version"]
models = sys.modules["app.services.job_orchestration.models"]
retry = sys.modules["app.services.job_orchestration.retry"]
queue_mod = sys.modules["app.services.job_orchestration.queue_manager"]
orch = sys.modules["app.services.job_orchestration.orchestrator"]


def setup_function():
    orch.reset_orchestrator()
    orch.set_max_concurrent(8)


def test_version_unit():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 6
    assert version.SPRINT == 4


def test_priority_queues():
    assert models.PRIORITY_ORDER["critical"] < models.PRIORITY_ORDER["high"]
    assert models.PRIORITY_ORDER["high"] < models.PRIORITY_ORDER["normal"]
    assert models.PRIORITY_ORDER["normal"] < models.PRIORITY_ORDER["low"]
    # Critical should dequeue before low
    orch.set_max_concurrent(1)
    low = orch.create_job(prompt="low priority job", priority="low", auto_process=False, metadata={"work_ms": 1})
    crit = orch.create_job(prompt="critical job", priority="critical", auto_process=False, metadata={"work_ms": 1})
    first = queue_mod.queue_manager.dequeue()
    assert first is not None
    assert first.job_id == crit["job_id"]


def test_create_and_complete_lifecycle():
    created = orch.create_job(prompt="Generate a short text summary", priority="high", metadata={"work_ms": 1})
    assert created["state"] in ("queued", "preparing", "running", "waiting", "completed")
    job = orch.wait_for_job(created["job_id"], timeout_sec=5.0)
    assert job is not None
    assert job.state == "completed"
    assert job.progress == 1.0
    assert job.metrics.success is True
    assert job.metrics.queue_time_ms >= 0
    assert job.metrics.processing_time_ms >= 0
    assert job.metrics.total_time_ms >= 0
    fetched = orch.get_job(created["job_id"])
    assert fetched is not None
    assert fetched["state"] == "completed"


def test_exponential_backoff_retry():
    d0 = retry.backoff_seconds(0, jitter=False)
    d1 = retry.backoff_seconds(1, jitter=False)
    d2 = retry.backoff_seconds(2, jitter=False)
    assert d1 > d0
    assert d2 > d1
    assert retry.can_retry(0, 3) is True
    assert retry.can_retry(3, 3) is False

    created = orch.create_job(
        prompt="force fail once then succeed",
        priority="normal",
        metadata={"force_fail_once": True, "work_ms": 1},
        max_retries=2,
    )
    job = orch.wait_for_job(created["job_id"], timeout_sec=8.0)
    assert job is not None
    assert job.state == "completed"
    assert job.retry_count >= 1


def test_cancel_and_manual_retry():
    created = orch.create_job(prompt="cancel me", priority="normal", auto_process=False)
    cancelled = orch.cancel_job(created["job_id"])
    assert cancelled["state"] == "cancelled"
    retried = orch.retry_job(created["job_id"])
    assert retried["state"] in ("queued", "retrying", "preparing", "running", "completed")
    job = orch.wait_for_job(created["job_id"], timeout_sec=5.0)
    assert job is not None
    assert job.state == "completed"


def test_job_dependencies():
    parent = orch.create_job(prompt="parent job", priority="high", metadata={"work_ms": 1})
    child = orch.create_job(
        prompt="child job",
        priority="normal",
        depends_on=[parent["job_id"]],
        metadata={"work_ms": 1},
    )
    child_job = orch.wait_for_job(child["job_id"], timeout_sec=8.0)
    parent_job = orch.wait_for_job(parent["job_id"], timeout_sec=2.0)
    assert parent_job is not None and parent_job.state == "completed"
    assert child_job is not None and child_job.state == "completed"


def test_status_history_metrics():
    for i in range(5):
        created = orch.create_job(prompt=f"batch job {i}", metadata={"work_ms": 1})
        orch.wait_for_job(created["job_id"], timeout_sec=5.0)
    status = orch.jobs_status()
    assert status["ok"] is True
    assert status["completed"] >= 5
    assert status["success_rate"] >= 80
    hist = orch.jobs_history(limit=10)
    assert hist["count"] >= 5
    assert "avg_queue_time_ms" in status


def test_load_testing_100_jobs():
    orch.set_max_concurrent(16)
    t0 = time.perf_counter()
    ids = []
    for i in range(100):
        priority = ("critical", "high", "normal", "low")[i % 4]
        created = orch.create_job(
            prompt=f"load test job {i}",
            priority=priority,
            metadata={"work_ms": 1},
        )
        ids.append(created["job_id"])
    done = 0
    deadline = time.perf_counter() + 30.0
    while time.perf_counter() < deadline and done < 100:
        orch.pump_scheduler()
        done = 0
        for jid in ids:
            j = orch.get_job(jid)
            if j and j["state"] in ("completed", "failed", "cancelled"):
                done += 1
        if done < 100:
            time.sleep(0.02)
    elapsed = time.perf_counter() - t0
    status = orch.jobs_status()
    assert done == 100
    assert status["completed"] >= 95
    assert elapsed < 25.0
    assert status["avg_total_time_ms"] < 5000
    # throughput
    jps = 100 / elapsed if elapsed > 0 else 0
    assert jps > 5


def test_concurrent_execution_cap():
    orch.set_max_concurrent(3)
    ids = [
        orch.create_job(prompt=f"conc {i}", auto_process=True, metadata={"work_ms": 20})["job_id"]
        for i in range(6)
    ]
    # briefly observe active workers never exceed cap significantly
    peaks = []
    for _ in range(20):
        orch.pump_scheduler()
        peaks.append(orch.jobs_status()["active_workers"])
        time.sleep(0.01)
    assert max(peaks) <= 3
    for jid in ids:
        orch.wait_for_job(jid, timeout_sec=5.0)

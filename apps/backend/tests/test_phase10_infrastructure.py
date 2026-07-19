"""Phase 10 Sprint 4 — Infrastructure scalability & recovery validation."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVC = ROOT / "app" / "services"
JO = SVC / "job_orchestration"
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


def _bootstrap_jo():
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
        "dead_letter",
        "retry",
        "queue_manager",
        "metrics",
        "orchestrator",
    ):
        _load(f"app.services.job_orchestration.{name}", JO / f"{name}.py")
    # Wire package exports
    orch = sys.modules["app.services.job_orchestration.orchestrator"]
    jo_pkg = sys.modules["app.services.job_orchestration"]
    for attr in (
        "create_job",
        "wait_for_job",
        "reset_orchestrator",
        "set_max_concurrent",
        "jobs_status",
        "recover_workers",
        "recover_from_dlq",
        "dead_letter_status",
        "pump_scheduler",
    ):
        setattr(jo_pkg, attr, getattr(orch, attr))
    return jo_pkg


def _load_infra():
    _bootstrap_jo()
    # Make `from app.services import job_orchestration` work
    if "app.services" not in sys.modules:
        _ensure_parents("app.services")
    svc = sys.modules["app.services"]
    svc.job_orchestration = sys.modules["app.services.job_orchestration"]
    return _load(
        "app.services.phase10_infrastructure",
        SVC / "phase10_infrastructure.py",
    )


def test_inventory_and_scalability_matrix():
    infra = _load_infra()
    inv = infra.infrastructure_inventory()
    assert inv["componentCount"] >= 10
    scale = infra.scalability_matrix()
    users = [t["concurrentUsers"] for t in scale["tiers"]]
    assert users == [100, 500, 1000, 5000, 10000]
    assert scale["horizontalReady"] is True


def test_queue_has_dlq_and_backpressure():
    jo = _bootstrap_jo()
    status = jo.jobs_status()
    assert status["max_queue_depth"] >= 1000
    assert "dead_letter" in status
    assert status["dead_letter"]["maxDepth"] >= 100


def test_dlq_and_recovery():
    jo = _bootstrap_jo()
    jo.reset_orchestrator()
    created = jo.create_job(
        prompt="force dlq",
        metadata={"force_fail_once": True, "work_ms": 1},
        max_retries=0,
    )
    job = jo.wait_for_job(created["job_id"], timeout_sec=8.0)
    assert job is not None and job.state == "failed"
    dlq = jo.dead_letter_status()
    assert dlq["depth"] >= 1
    jo.recover_from_dlq(created["job_id"])
    again = jo.wait_for_job(created["job_id"], timeout_sec=8.0)
    assert again is not None and again.state == "completed"


def test_recover_workers():
    jo = _bootstrap_jo()
    jo.reset_orchestrator()
    jo.set_max_concurrent(4)
    for i in range(20):
        jo.create_job(prompt=f"worker recover {i}", metadata={"work_ms": 1})
    rec = jo.recover_workers()
    assert rec["ok"] is True
    time.sleep(0.5)
    jo.pump_scheduler()


def test_backpressure_rejects_when_full():
    jo = _bootstrap_jo()
    jo.reset_orchestrator()
    ver = sys.modules["app.services.job_orchestration.version"]
    original = ver.MAX_QUEUE_DEPTH
    try:
        ver.MAX_QUEUE_DEPTH = 3
        # Patch orchestrator constant binding
        orch = sys.modules["app.services.job_orchestration.orchestrator"]
        orch.MAX_QUEUE_DEPTH = 3
        jo.set_max_concurrent(1)
        # Fill without processing
        for i in range(3):
            jo.create_job(
                prompt=f"bp {i}",
                metadata={"work_ms": 50},
                auto_process=False,
            )
        try:
            jo.create_job(prompt="overflow", auto_process=False)
            assert False, "expected backpressure"
        except ValueError as exc:
            assert "backpressure" in str(exc).lower()
    finally:
        ver.MAX_QUEUE_DEPTH = original
        orch.MAX_QUEUE_DEPTH = original
        jo.reset_orchestrator()


def test_cache_inventory():
    infra = _load_infra()
    cache = infra.cache_inventory()
    assert len(cache["layers"]) >= 4
    assert cache["duplicateCachingRemoved"] is False


def test_recovery_suite():
    infra = _load_infra()
    result = infra.recovery_suite()
    assert result["ok"] is True
    assert result["checks"]["autoRetry"] is True
    assert result["checks"]["deadLetterRecovery"] is True


def test_stress_100_250_500_1000():
    infra = _load_infra()
    # Cap concurrent for CI speed; still validates batches.
    result = infra.run_stress_batches((100, 250, 500, 1000), max_concurrent=32)
    assert result["ok"] is True
    assert len(result["batches"]) == 4
    for batch in result["batches"]:
        assert batch["failures"] == 0
        assert batch["successRate"] == 1.0
        assert batch["queueStable"] is True


def test_full_report_scores():
    infra = _load_infra()
    report = infra.full_report(run_stress=False)
    assert report["phase"] == 10 and report["sprint"] == 4
    scores = report["scores"]
    assert scores["overallProductionReadinessPct"] >= 80
    assert scores["grade"] in ("A", "A-", "B+", "B")


def test_routes_and_ready_probe_source():
    routes = (ROOT / "app" / "api" / "routes" / "infrastructure.py").read_text(
        encoding="utf-8"
    )
    assert "/infrastructure" in routes or 'prefix="/infrastructure"' in routes
    health = (ROOT / "app" / "api" / "routes" / "health.py").read_text(encoding="utf-8")
    assert "phase10_infrastructure_validated" in health
    assert '"sprint": 4' in health or "sprint\": 4" in health


def test_redis_reconnect_helper_source():
    path = (
        ROOT.parent.parent
        / "packages"
        / "utils"
        / "src"
        / "server"
        / "persistent-store.ts"
    )
    if not path.exists():
        path = (
            ROOT.parents[1]
            / "packages"
            / "utils"
            / "src"
            / "server"
            / "persistent-store.ts"
        )
    text = path.read_text(encoding="utf-8")
    assert "resetRedisClient" in text
    assert "withRedisRetry" in text


def test_prisma_singleton_production():
    path = (
        ROOT.parent.parent
        / "packages"
        / "utils"
        / "src"
        / "server"
        / "prisma.ts"
    )
    if not path.exists():
        path = ROOT.parents[1] / "packages" / "utils" / "src" / "server" / "prisma.ts"
    text = path.read_text(encoding="utf-8")
    assert "globalForPrisma.prisma = prisma" in text
    assert "NODE_ENV !== \"production\"" not in text

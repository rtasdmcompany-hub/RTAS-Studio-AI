"""Phase 6 Sprint 9 — AI Enterprise Monitoring, Observability & Self-Healing tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MO = ROOT / "app" / "services" / "monitoring_observability"

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


def _load_pkg():
    _ensure_parents("app.services.monitoring_observability")
    pkg = type(sys)("app.services.monitoring_observability")
    pkg.__path__ = [str(MO)]
    sys.modules["app.services.monitoring_observability"] = pkg
    for name in (
        "version",
        "models",
        "store",
        "health_monitor",
        "alerts",
        "incidents",
        "self_healing",
        "diagnostics",
        "predictive",
        "metrics",
        "engine",
    ):
        _load(f"app.services.monitoring_observability.{name}", MO / f"{name}.py")
    eng = sys.modules["app.services.monitoring_observability.engine"]
    ver = sys.modules["app.services.monitoring_observability.version"]
    pkg.ENGINE_NAME = ver.ENGINE_NAME
    pkg.ENGINE_VERSION = ver.ENGINE_VERSION
    pkg.ENGINE_LABEL = ver.ENGINE_LABEL
    pkg.get_monitoring_engine = eng.get_monitoring_engine
    pkg.reset_engine = eng.reset_engine


_load_pkg()

version = sys.modules["app.services.monitoring_observability.version"]
store = sys.modules["app.services.monitoring_observability.store"]
predictive = sys.modules["app.services.monitoring_observability.predictive"]
engine_mod = sys.modules["app.services.monitoring_observability.engine"]


def setup_function():
    engine_mod.reset_engine()


def test_version_unit():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 6
    assert version.SPRINT == 9


def test_health_monitors_core_components():
    eng = engine_mod.get_monitoring_engine()
    health = eng.health()
    names = {c["name"] for c in health["components"]}
    for required in (
        "api",
        "ai_providers",
        "queue",
        "database",
        "redis",
        "supabase",
        "paddle",
        "storage",
        "gpu_workers",
        "cpu",
        "memory",
        "disk",
        "network",
    ):
        assert required in names
    assert health["overall"] in ("healthy", "degraded", "unhealthy")


def test_metrics_and_dashboard_payload():
    eng = engine_mod.get_monitoring_engine()
    for i in range(20):
        eng.record_request(success=i % 5 != 0, latency_ms=40 + i)
    m = eng.metrics()
    assert "request_rate" in m
    assert "success_rate" in m
    assert "failure_rate" in m
    assert "avg_response_ms" in m
    assert "queue_latency_ms" in m
    assert "provider_latency_ms" in m
    assert "active_jobs" in m
    assert "dashboard" in m
    assert "charts" in m["dashboard"]


def test_alerts_on_provider_offline():
    eng = engine_mod.get_monitoring_engine()
    eng.simulate_failure("ai_providers")
    eng.health()
    al = eng.alerts()
    types = {a["alert_type"] for a in al["alerts"]}
    assert "provider_offline" in types


def test_incidents_and_recovery_self_healing():
    eng = engine_mod.get_monitoring_engine()
    store.set_worker("worker_x", "failed")
    store.mark_stuck_job("job_stuck_1")
    store.set_queue_depth(5)
    eng.simulate_failure("queue")
    eng.health()
    incs = eng.incidents()
    assert incs["count"] >= 1
    rec = eng.recovery(
        {
            "component": "queue",
            "actions": [
                "detect_deadlock",
                "restart_worker",
                "retry_job",
                "recover_queue",
                "reconnect_service",
                "refresh_token",
                "failover",
            ],
            "job_ids": ["job_stuck_1"],
        }
    )
    assert rec["ok"] is True
    assert rec["count"] >= 1
    assert store.queue_depth() == 0
    assert "job_stuck_1" not in store.stuck_jobs()
    worker = next(w for w in store.workers() if w["worker_id"] == "worker_x")
    assert worker["status"] == "online"


def test_failover_providers():
    eng = engine_mod.get_monitoring_engine()
    store.set_provider_state("fal", "offline")
    eng.simulate_failure("ai_providers")
    before = eng.health()
    assert before["overall"] in ("unhealthy", "degraded")
    rec = eng.recovery({"component": "ai_providers", "actions": ["failover", "reconnect_service"]})
    assert rec["ok"] is True
    after = eng.health()
    providers = next(c for c in after["components"] if c["name"] == "ai_providers")
    assert providers["status"] in ("healthy", "degraded")


def test_predictive_failure_analyzer():
    eng = engine_mod.get_monitoring_engine()
    for i in range(30):
        eng.record_request(success=True, latency_ms=50)
    for i in range(30):
        eng.record_request(success=False, latency_ms=900)
    store.set_queue_depth(80)
    store.mark_stuck_job("j1")
    pred = predictive.analyze()
    assert pred["risk_score"] >= 25
    assert pred["recommendation"]


def test_system_status_bundle():
    eng = engine_mod.get_monitoring_engine()
    status = eng.status()
    assert status["engine"]
    assert "health" in status
    assert "metrics" in status
    assert "prediction" in status
    assert "self_healing" in status
    assert status["self_healing"]["enabled"] is True
    assert "dashboard" in status


def test_auth_failure_alert_path():
    from app.services.monitoring_observability import alerts as alerts_mod

    alerts_mod.raise_alert(
        "auth_failure",
        "authentication failures spike",
        component="api",
        level="error",
    )
    eng = engine_mod.get_monitoring_engine()
    al = eng.alerts()
    assert any(a["alert_type"] == "auth_failure" for a in al["alerts"])


def test_stress_health_and_metrics():
    eng = engine_mod.get_monitoring_engine()
    t0 = time.perf_counter()
    for i in range(200):
        eng.record_request(success=i % 7 != 0, latency_ms=20 + (i % 40))
        if i % 25 == 0:
            eng.health()
            eng.metrics()
    status = eng.status()
    elapsed = time.perf_counter() - t0
    assert status["metrics"]["success_rate"] > 0
    assert elapsed < 5.0

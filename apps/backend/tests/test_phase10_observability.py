"""Phase 10 Sprint 7 — Observability & Operational Excellence tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_alert_types_include_ops_excellence():
    from app.services.monitoring_observability.alerts import ALERT_TYPES

    assert "worker_failure" in ALERT_TYPES
    assert "security_event" in ALERT_TYPES
    assert "auth_failure" in ALERT_TYPES


def test_evaluate_components_raises_worker_auth_security():
    from app.services.monitoring_observability import alerts, health_monitor, store

    store.set_worker("sprint7-worker", "failed")
    store.force_failure("authentication")
    store.force_failure("security")
    report = health_monitor.collect_health()
    raised = alerts.evaluate_components(report.components)
    types = {a.get("alert_type") for a in raised}
    assert "worker_failure" in types
    assert "auth_failure" in types
    assert "security_event" in types
    store.clear_failure("authentication")
    store.clear_failure("security")


def test_correlation_middleware_exists():
    from app.middleware.correlation import CorrelationIdMiddleware

    assert CorrelationIdMiddleware is not None
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "CorrelationIdMiddleware" in main


def test_runbooks_present():
    from app.services.phase10_observability import runbooks

    listed = runbooks.list_runbooks()
    assert listed["ok"] is True
    assert listed["count"] >= 8


def test_obs_service_status():
    from app.services.phase10_observability import (
        get_phase10_observability_service,
        reset_phase10_observability_service,
    )

    reset_phase10_observability_service()
    st = get_phase10_observability_service().status()
    assert st["phase"] == 10 and st["sprint"] == 7


def test_observability_audit():
    from app.services.phase10_observability import get_phase10_observability_service

    result = get_phase10_observability_service().observability_audit()
    assert result["ok"] is True
    assert result["observabilityScore"] >= 90
    assert len(result["inspected"]) == 11


def test_logging_architecture():
    from app.services.phase10_observability import get_phase10_observability_service

    result = get_phase10_observability_service().verify_logging()
    assert result["ok"] is True
    assert result["structuredLogging"] is True
    assert result["logCorrelation"] is True


def test_monitoring_coverage():
    from app.services.phase10_observability import get_phase10_observability_service

    result = get_phase10_observability_service().monitoring_coverage()
    assert result["ok"] is True, result
    assert result["monitoringScore"] == 100.0


def test_alerting_readiness():
    from app.services.phase10_observability import get_phase10_observability_service

    result = get_phase10_observability_service().verify_alerting()
    assert result["ok"] is True, result
    assert result["alertReadiness"] is True


def test_health_verification():
    from app.services.phase10_observability import get_phase10_observability_service

    result = get_phase10_observability_service().health_verification()
    assert result["ok"] is True, result


def test_operational_readiness():
    from app.services.phase10_observability import get_phase10_observability_service

    result = get_phase10_observability_service().operational_readiness()
    assert result["ok"] is True, result


def test_monitoring_validation_and_report():
    from app.services.phase10_observability import get_phase10_observability_service

    validation = get_phase10_observability_service().monitoring_validation()
    assert validation["ok"] is True, validation

    report = get_phase10_observability_service().full_report()
    assert report["ok"] is True, report.get("scores")
    assert report["observabilityVerified"] is True
    assert report["alertingVerified"] is True
    assert report["operationalExcellenceVerified"] is True
    scores = report["scores"]
    assert scores["overallScore"] >= 88
    assert scores["overallGrade"] in ("A", "A-", "B+")


def test_routes_and_ready_probe():
    routes = (ROOT / "app" / "api" / "routes" / "observability.py").read_text(
        encoding="utf-8"
    )
    assert 'prefix="/observability"' in routes
    health = (ROOT / "app" / "api" / "routes" / "health.py").read_text(encoding="utf-8")
    assert "phase10_observability_verified" in health
    assert "phase10_alerting_verified" in health
    assert "phase10_operational_excellence_verified" in health
    assert "phase10_sprint" in health
    router = (ROOT / "app" / "api" / "router.py").read_text(encoding="utf-8")
    assert "observability" in router

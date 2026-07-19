"""Phase 10 Sprint 6 — Disaster Recovery & High Availability tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_backup_store_integrity_and_restore():
    from app.services.phase10_disaster_recovery import backup_store

    backup_store.clear()
    snap = backup_store.create_snapshot("configuration", {"a": 1})
    assert snap["integrity"] == "ok"
    restored = backup_store.restore_snapshot(snap["snapshotId"])
    assert restored["ok"] is True
    assert backup_store.verify_integrity()["ok"] is True


def test_alert_types_include_dr():
    from app.services.monitoring_observability.alerts import ALERT_TYPES

    assert "backup_failure" in ALERT_TYPES
    assert "recovery_failure" in ALERT_TYPES


def test_self_healing_restarts_orchestrator_pool():
    from app.services.monitoring_observability import self_healing, store
    from app.services import job_orchestration as jo

    jo.reset_orchestrator()
    store.set_worker("dr_test_worker", "failed")
    results = self_healing.restart_failed_workers()
    assert any(r.get("target") == "job_orchestration" for r in results)
    assert any(r.get("success") for r in results)


def test_dr_service_status():
    from app.services.phase10_disaster_recovery import (
        get_phase10_disaster_recovery_service,
        reset_phase10_disaster_recovery_service,
    )

    reset_phase10_disaster_recovery_service()
    st = get_phase10_disaster_recovery_service().status()
    assert st["phase"] == 10 and st["sprint"] == 6


def test_disaster_recovery_audit():
    from app.services.phase10_disaster_recovery import get_phase10_disaster_recovery_service

    result = get_phase10_disaster_recovery_service().disaster_recovery_audit()
    assert result["ok"] is True
    assert result["recoveryScore"] >= 90
    assert len(result["inspected"]) == 9


def test_backup_strategy():
    from app.services.phase10_disaster_recovery import get_phase10_disaster_recovery_service

    result = get_phase10_disaster_recovery_service().run_backup_cycle()
    assert result["ok"] is True
    assert "backupFrequency" in result
    assert result["backupIntegrity"]["ok"] is True
    assert result["restoreReadiness"]["ok"] is True


def test_recovery_simulation():
    from app.services.phase10_disaster_recovery import get_phase10_disaster_recovery_service

    result = get_phase10_disaster_recovery_service().simulate_recovery()
    assert result["ok"] is True, result
    assert result["recoverySuccessRate"] == 100.0
    assert result["meanTimeToRecoveryMs"] >= 0


def test_high_availability():
    from app.services.phase10_disaster_recovery import get_phase10_disaster_recovery_service

    result = get_phase10_disaster_recovery_service().verify_high_availability()
    assert result["ok"] is True, result
    assert result["availabilityScore"] == 100.0


def test_business_continuity():
    from app.services.phase10_disaster_recovery import get_phase10_disaster_recovery_service

    result = get_phase10_disaster_recovery_service().business_continuity()
    assert result["ok"] is True, result
    assert result["heavyLoad"]["failures"] == 0


def test_monitoring_and_alerting():
    from app.services.phase10_disaster_recovery import get_phase10_disaster_recovery_service

    result = get_phase10_disaster_recovery_service().verify_monitoring()
    assert result["ok"] is True, result
    assert result["requiredCoverage"] is True


def test_reliability_and_full_report():
    from app.services.phase10_disaster_recovery import get_phase10_disaster_recovery_service

    rel = get_phase10_disaster_recovery_service().reliability_tests()
    assert rel["ok"] is True
    assert rel["recoverySuccessRate"] == 100.0

    report = get_phase10_disaster_recovery_service().full_report()
    assert report["ok"] is True, report.get("scores")
    assert report["disasterRecoveryVerified"] is True
    assert report["highAvailabilityVerified"] is True
    scores = report["scores"]
    assert scores["overallScore"] >= 88
    assert scores["overallDisasterRecoveryGrade"] in ("A", "A-", "B+")


def test_routes_and_ready_probe():
    routes = (ROOT / "app" / "api" / "routes" / "disaster_recovery.py").read_text(
        encoding="utf-8"
    )
    assert 'prefix="/disaster-recovery"' in routes
    health = (ROOT / "app" / "api" / "routes" / "health.py").read_text(encoding="utf-8")
    assert "phase10_disaster_recovery_verified" in health
    assert "phase10_high_availability_verified" in health
    assert '"sprint": 6' in health or "sprint\": 6" in health
    router = (ROOT / "app" / "api" / "router.py").read_text(encoding="utf-8")
    assert "disaster_recovery" in router

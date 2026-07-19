"""Phase 10 Sprint 5 — AI QA & Release Candidate (RC-1) tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_provider_failover_genuine_fix():
    from app.services.provider_orchestration.manager import (
        get_provider_manager,
        reset_provider_manager,
    )
    import asyncio

    reset_provider_manager()
    mgr = get_provider_manager(refresh=True)
    result = asyncio.run(
        mgr.invoke_with_failover(
            "failover probe",
            capability="text",
            force_fail_first=True,
        )
    )
    assert result["success"] is True
    assert result["attempts"] >= 2
    assert any("forced" in x or "fail:" in x for x in result["failoverLog"])
    assert result.get("recovered") is True


def test_runpod_env_hints_include_v2():
    from app.services.provider_orchestration.builtins import builtin_provider_factories

    factories = builtin_provider_factories()
    runpod = None
    for factory in factories:
        p = factory()
        if p.provider_id == "runpod":
            runpod = p
            break
    assert runpod is not None
    assert "RUNPOD_API_KEY_V2" in runpod._env_key_hints


def test_rc_service_status():
    from app.services.phase10_rc_validation import get_phase10_rc_validation_service

    svc = get_phase10_rc_validation_service()
    st = svc.status()
    assert st["phase"] == 10 and st["sprint"] == 5
    assert st["rc"] == "RC-1"
    assert st["uiFrozen"] is True


def test_ai_generation_validation():
    from app.services.phase10_rc_validation import get_phase10_rc_validation_service

    result = get_phase10_rc_validation_service().validate_ai_generation()
    assert result["ok"] is True
    assert result["aiQualityScore"] >= 90
    assert result["passed"] == result["total"]


def test_e2e_workflow_validation():
    from app.services.phase10_rc_validation import get_phase10_rc_validation_service

    result = get_phase10_rc_validation_service().validate_e2e_workflow()
    assert result["ok"] is True, result
    assert result["workflowSuccessRate"] == 100.0


def test_provider_routing_validation():
    from app.services.phase10_rc_validation import get_phase10_rc_validation_service

    result = get_phase10_rc_validation_service().validate_provider_routing()
    assert result["ok"] is True, result
    assert all(result["providerPresent"].values())
    assert result["automaticFailover"] is True


def test_output_quality_validation():
    from app.services.phase10_rc_validation import get_phase10_rc_validation_service

    result = get_phase10_rc_validation_service().validate_output_quality()
    assert result["ok"] is True, result
    assert result["outputQualityScore"] >= 85


def test_rc1_modules_100_percent():
    from app.services.phase10_rc_validation import get_phase10_rc_validation_service

    result = get_phase10_rc_validation_service().validate_rc1_modules()
    assert result["ok"] is True, result
    assert result["passRate"] == 100.0
    assert result["passed"] == result["total"]


def test_regression_phases_1_through_10():
    from app.services.phase10_rc_validation import get_phase10_rc_validation_service

    result = get_phase10_rc_validation_service().validate_regression()
    assert result["ok"] is True, result
    for phase in range(1, 11):
        assert result["results"].get(f"phase_{phase}") is True


def test_full_rc_report_verified():
    from app.services.phase10_rc_validation import get_phase10_rc_validation_service

    report = get_phase10_rc_validation_service().full_validation()
    assert report["ok"] is True, report.get("report")
    assert report["rc1Status"] == "VERIFIED"
    assert report["report"]["productionReadinessPct"] >= 90
    assert report["report"]["remainingIssues"] == []


def test_routes_and_ready_probe():
    routes = (
        ROOT / "app" / "api" / "routes" / "phase10_rc_validation.py"
    ).read_text(encoding="utf-8")
    assert 'prefix="/phase10/rc"' in routes
    health = (ROOT / "app" / "api" / "routes" / "health.py").read_text(encoding="utf-8")
    assert "phase10_rc1_verified" in health
    assert "RC-1" in health
    assert '"sprint": 5' in health or "sprint\": 5" in health


def test_router_registers_rc():
    text = (ROOT / "app" / "api" / "router.py").read_text(encoding="utf-8")
    assert "phase10_rc_validation" in text

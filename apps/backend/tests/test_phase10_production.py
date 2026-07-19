"""Phase 10 Sprint 9 — Production Environment & RC-2 tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_secret_catalog_expanded():
    from app.services.enterprise_security.secrets import SENSITIVE_ENV_KEYS

    for key in (
        "PAYPAL_CLIENT_ID",
        "RESEND_API_KEY",
        "GITHUB_TOKEN",
        "GEMINI_API_KEY",
        "NEXTAUTH_SECRET",
        "UPSTASH_REDIS_REST_TOKEN",
    ):
        assert key in SENSITIVE_ENV_KEYS


def test_rotation_plan_does_not_rotate():
    from app.services.phase10_production import secret_rotation

    plan = secret_rotation.secret_rotation_checklist()
    assert plan["rotatedAnySecret"] is False
    assert plan["secretsModified"] is False
    assert plan["count"] == 12


def test_env_inventory_no_env_mutation():
    from app.services.phase10_production import env_inventory

    inv = env_inventory.build_environment_inventory()
    assert inv["ok"] is True
    assert inv["envFilesModified"] is False
    assert all(i["valueExposed"] is False for i in inv["items"])


def test_service_status_rc2():
    from app.services.phase10_production import (
        get_phase10_production_service,
        reset_phase10_production_service,
        RC_LABEL,
    )

    reset_phase10_production_service()
    st = get_phase10_production_service().status()
    assert st["phase"] == 10 and st["sprint"] == 9
    assert st["releaseCandidate"] == RC_LABEL == "RC-2"
    assert st["secretsModified"] is False


def test_production_environment_and_deploy():
    from app.services.phase10_production import get_phase10_production_service

    env = get_phase10_production_service().production_environment_audit()
    assert env["ok"] is True, env
    deploy = get_phase10_production_service().deployment_pipeline_audit()
    assert deploy["ok"] is True, deploy


def test_rc2_validation_100_percent():
    from app.services.phase10_production import get_phase10_production_service

    result = get_phase10_production_service().run_rc2_validation()
    assert result["ok"] is True, result
    assert result["passRate"] == 100.0
    assert result["passed"] == result["total"]


def test_smoke_and_report():
    from app.services.phase10_production import get_phase10_production_service

    smoke = get_phase10_production_service().production_smoke_tests()
    assert smoke["ok"] is True, smoke

    report = get_phase10_production_service().full_report()
    assert report["ok"] is True, report.get("scores")
    assert report["rc2Verified"] is True
    assert report["productionEnvironmentVerified"] is True
    assert report["readyForFinalRelease"] is True
    assert report["secretsModified"] is False
    assert report["envFilesModified"] is False
    scores = report["scores"]
    assert scores["overallProductionReadinessPct"] >= 88
    assert scores["releaseCandidateStatus"] == "RC-2"


def test_launch_checklist():
    from app.services.phase10_production import get_phase10_production_service

    launch = get_phase10_production_service().final_launch_checklist()
    assert launch["ok"] is True
    assert launch["blockingRemaining"] >= 1


def test_routes_and_ready_probe():
    routes = (ROOT / "app" / "api" / "routes" / "phase10_rc2.py").read_text(encoding="utf-8")
    assert 'prefix="/phase10/rc2"' in routes
    health = (ROOT / "app" / "api" / "routes" / "health.py").read_text(encoding="utf-8")
    assert "phase10_rc2_verified" in health
    assert "phase10_production_environment_verified" in health
    assert "ready_for_final_release" in health
    assert '"sprint": 9' in health or "sprint\": 9" in health
    assert "RC-2" in health
    router = (ROOT / "app" / "api" / "router.py").read_text(encoding="utf-8")
    assert "phase10_rc2" in router

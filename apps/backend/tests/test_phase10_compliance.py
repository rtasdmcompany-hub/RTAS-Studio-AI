"""Phase 10 Sprint 8 — Legal Compliance & Enterprise Release tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPO = ROOT.parents[1]


def test_license_and_notice_present():
    assert (REPO / "LICENSE").is_file()
    assert (REPO / "NOTICE").is_file()


def test_dsr_export_and_erase():
    from app.services.phase10_compliance import dsr_store

    dsr_store.clear()
    dsr_store.upsert_user_profile("u1", {"email": "a@b.c"})
    export = dsr_store.export_user_data("u1")
    assert export["status"] == "completed"
    assert export["result"]["portable"] is True
    erase = dsr_store.delete_user_account("u1")
    assert erase["result"]["erased"] is True


def test_policy_catalog_complete():
    from app.services.phase10_compliance import policy_catalog

    listed = policy_catalog.list_policies()
    assert listed["count"] >= 8
    for key in (
        "privacy_policy",
        "terms_of_service",
        "cookie_policy",
        "acceptable_use_policy",
        "refund_policy",
        "subscription_policy",
    ):
        assert key in listed["required"]


def test_compliance_service_status():
    from app.services.phase10_compliance import (
        get_phase10_compliance_service,
        reset_phase10_compliance_service,
    )

    reset_phase10_compliance_service()
    st = get_phase10_compliance_service().status()
    assert st["phase"] == 10 and st["sprint"] == 8


def test_legal_compliance_audit():
    from app.services.phase10_compliance import get_phase10_compliance_service

    result = get_phase10_compliance_service().legal_compliance_audit()
    assert result["ok"] is True, result
    assert result["legalComplianceScore"] >= 90


def test_privacy_audit():
    from app.services.phase10_compliance import get_phase10_compliance_service

    result = get_phase10_compliance_service().privacy_audit()
    assert result["ok"] is True, result
    assert result["privacyScore"] == 100.0


def test_compliance_matrix():
    from app.services.phase10_compliance import get_phase10_compliance_service

    result = get_phase10_compliance_service().compliance_matrix()
    assert result["ok"] is True
    assert "GDPR" in result["matrix"]
    assert "OWASP_Top_10" in result["matrix"]
    assert "PCI_Aware_Billing" in result["matrix"]


def test_third_party_readiness():
    from app.services.phase10_compliance import get_phase10_compliance_service

    result = get_phase10_compliance_service().third_party_readiness()
    assert result["ok"] is True
    assert len(result["inspected"]) == 12
    assert all(v["secretsModified"] is False for v in result["providers"].values())


def test_licensing_and_docs():
    from app.services.phase10_compliance import get_phase10_compliance_service

    lic = get_phase10_compliance_service().licensing_audit()
    assert lic["ok"] is True, lic
    docs = get_phase10_compliance_service().documentation_audit()
    assert docs["ok"] is True, docs


def test_enterprise_release_and_report():
    from app.services.phase10_compliance import get_phase10_compliance_service

    rel = get_phase10_compliance_service().enterprise_release_readiness()
    assert rel["ok"] is True
    assert rel["riskAssessment"]

    report = get_phase10_compliance_service().full_report()
    assert report["ok"] is True, report.get("scores")
    assert report["legalComplianceVerified"] is True
    assert report["privacyVerified"] is True
    assert report["licensingVerified"] is True
    assert report["enterpriseReleaseReady"] is True
    scores = report["scores"]
    assert scores["overallProductionCompliancePct"] >= 88


def test_privacy_controls_dsr_pointer():
    from app.services.enterprise_security.compliance import privacy_controls

    caps = privacy_controls()
    assert caps["dsr_api"] == "/api/compliance/dsr"
    assert caps["right_to_erasure_supported"] is True


def test_routes_and_ready_probe():
    routes = (ROOT / "app" / "api" / "routes" / "compliance.py").read_text(encoding="utf-8")
    assert 'prefix="/compliance"' in routes
    assert "/dsr/export" in routes
    health = (ROOT / "app" / "api" / "routes" / "health.py").read_text(encoding="utf-8")
    assert "phase10_legal_compliance_verified" in health
    assert "phase10_privacy_verified" in health
    assert "phase10_licensing_verified" in health
    assert "phase10_enterprise_release_ready" in health
    assert '"sprint": 8' in health or "sprint\": 8" in health
    router = (ROOT / "app" / "api" / "router.py").read_text(encoding="utf-8")
    assert "compliance" in router

"""Phase 9 Sprint 10 — Final Integration, Regression, Load/Stress & Production Validation.

Ties together every Phase 9 Marketplace Ecosystem engine and validates end-to-end
workflows, load/stress behaviour, security, and production readiness. Backend only.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVC = ROOT / "app" / "services"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("RTAS_JWT_SECRET", "phase9-final-jwt-secret-key-32bytes")
os.environ.setdefault("AI_BACKEND_SECRET", "phase9-final-backend-secret-32bytes")


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


def _load_folder(folder: str, modules: tuple[str, ...]):
    path = SVC / folder
    pkg = f"app.services.{folder}"
    _ensure_parents(pkg)
    mod = type(sys)(pkg)
    mod.__path__ = [str(path)]
    sys.modules[pkg] = mod
    for name in modules:
        _load(f"{pkg}.{name}", path / f"{name}.py")
    return mod


def _wire_getter(pkg: str, getter: str):
    mod = sys.modules[f"app.services.{pkg}"]
    svc = sys.modules[f"app.services.{pkg}.service"]
    setattr(mod, getter, getattr(svc, getter))
    if hasattr(svc, "reset_engine"):
        setattr(mod, "reset_engine", svc.reset_engine)


def _bootstrap():
    _load_folder(
        "multi_tenant",
        ("version", "roles", "models", "validation", "store", "repository", "service", "engine"),
    )
    _wire_getter("multi_tenant", "get_multi_tenant_service")

    _load_folder(
        "enterprise_auth",
        (
            "version", "errors", "models", "store", "audit", "permission_engine",
            "sessions", "validators", "middleware", "sso", "service", "engine",
        ),
    )
    ea = sys.modules["app.services.enterprise_auth"]
    ea.get_enterprise_auth_service = sys.modules[
        "app.services.enterprise_auth.service"
    ].get_enterprise_auth_service
    ea.reset_engine = sys.modules["app.services.enterprise_auth.service"].reset_engine
    ea.require_access = sys.modules["app.services.enterprise_auth.middleware"].require_access

    # Phase 8 commerce + collaboration dependencies for e2e
    deps = (
        ("billing", ("version", "catalog", "models", "store", "service", "engine"), "get_billing_service"),
        (
            "payment_processing",
            ("version", "catalog", "models", "store", "signatures", "service", "engine"),
            "get_payment_processing_service",
        ),
        (
            "credit_metering",
            ("version", "catalog", "models", "store", "service", "engine"),
            "get_credit_metering_service",
        ),
        (
            "billing_automation",
            ("version", "catalog", "models", "store", "service", "engine"),
            "get_billing_automation_service",
        ),
        ("marketplace", ("version", "catalog", "models", "store", "service", "engine"), "get_marketplace_service"),
        (
            "project_collaboration",
            ("version", "roles", "models", "store", "permissions", "service", "engine"),
            "get_project_collaboration_service",
        ),
        (
            "asset_library",
            ("version", "catalog", "models", "store", "service", "engine"),
            "get_asset_library_service",
        ),
    )
    for pkg, modules, getter in deps:
        _load_folder(pkg, modules)
        _wire_getter(pkg, getter)

    # Phase 9 engines (standard layout)
    for pkg, getter in (
        ("marketplace_ecosystem", "get_marketplace_ecosystem_service"),
        ("creator_platform", "get_creator_platform_service"),
        ("community_platform", "get_community_platform_service"),
        ("template_store", "get_template_store_service"),
        ("plugin_framework", "get_plugin_framework_service"),
        ("public_api_platform", "get_public_api_platform_service"),
        ("agent_orchestration", "get_agent_orchestration_service"),
        ("enterprise_automation", "get_enterprise_automation_service"),
        ("marketplace_revenue", "get_marketplace_revenue_service"),
    ):
        _load_folder(
            pkg, ("version", "catalog", "models", "store", "service", "engine")
        )
        _wire_getter(pkg, getter)

    _load_folder(
        "phase9_final_validation",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    _wire_getter("phase9_final_validation", "get_phase9_final_validation_service")


_bootstrap()


def _p9():
    return sys.modules["app.services.phase9_final_validation.service"]


def _mt():
    return sys.modules["app.services.multi_tenant.service"]


def _version():
    return sys.modules["app.services.phase9_final_validation.version"]


def _catalog():
    return sys.modules["app.services.phase9_final_validation.catalog"]


def _errors():
    return sys.modules["app.services.enterprise_auth.errors"]


_RESET_PKGS = (
    "payment_processing",
    "credit_metering",
    "billing_automation",
    "marketplace",
    "project_collaboration",
    "asset_library",
    "marketplace_ecosystem",
    "creator_platform",
    "community_platform",
    "template_store",
    "plugin_framework",
    "public_api_platform",
    "agent_orchestration",
    "enterprise_automation",
    "marketplace_revenue",
    "phase9_final_validation",
)


def setup_function():
    _bootstrap()
    for pkg in _RESET_PKGS:
        key = f"app.services.{pkg}.service"
        if key not in sys.modules:
            continue
        mod = sys.modules[key]
        if hasattr(mod, "_service"):
            mod._service = None
        store_key = f"app.services.{pkg}.store"
        if store_key in sys.modules and hasattr(sys.modules[store_key], "reset_store"):
            sys.modules[store_key].reset_store()
    _mt().reset_engine()
    sys.modules["app.services.enterprise_auth.service"].reset_engine()


def _svc():
    return _p9().get_phase9_final_validation_service()


# =========================================================================
# Unit
# =========================================================================


def test_version_unit():
    v = _version()
    assert v.PHASE == 9
    assert v.SPRINT == 10
    assert v.PHASE_STATUS == "COMPLETE"
    assert v.READY_FOR_PHASE_10 is True


def test_catalog_unit():
    c = _catalog()
    assert len(c.PHASE9_ENGINE_PACKAGES) == 9
    assert 50 in c.LOAD_BATCHES and 1000 in c.LOAD_BATCHES
    assert "rbac" in c.SECURITY_CHECKS
    assert c.clamp_score(150) == 100.0
    assert c.aggregate_scores({"a": 100.0, "b": 90.0}) == 95.0


def test_engine_status_unit():
    status = _svc().status()
    assert status["ok"] is True
    assert status["phase"] == 9
    assert status["sprint"] == 10
    assert status["readyForPhase10"] is True
    assert len(status["engines"]) == 6
    assert all(v == "ready" for v in status["engines"].values())


# =========================================================================
# Phase 9 module verification
# =========================================================================


def test_all_phase9_modules_verified():
    result = _svc().modules.verify()
    assert result["ok"] is True
    assert result["score"] == 100.0
    for eng in result["engines"]:
        assert eng["ok"] is True, eng
    verified = [m for m in result["modules"] if m["verified"]]
    assert len(verified) == len(result["modules"])


def test_phase9_sprint_numbers():
    expected = {
        "marketplace_ecosystem": 1,
        "creator_platform": 2,
        "community_platform": 3,
        "template_store": 4,
        "plugin_framework": 5,
        "public_api_platform": 6,
        "agent_orchestration": 7,
        "enterprise_automation": 8,
        "marketplace_revenue": 9,
    }
    for pkg, sprint in expected.items():
        ver = sys.modules[f"app.services.{pkg}.version"]
        assert ver.PHASE == 9, pkg
        assert ver.SPRINT == sprint, pkg


# =========================================================================
# Regression
# =========================================================================


def test_regression_phases_1_through_9():
    result = _svc().regression.run()
    assert result["ok"] is True
    assert result["phases"] == list(range(1, 10))
    for cap in _catalog().REGRESSION_CAPABILITIES:
        assert result["capabilities"][cap] is True


# =========================================================================
# End-to-end marketplace ecosystem workflow
# =========================================================================


def test_end_to_end_marketplace_ecosystem_workflow():
    result = _svc().e2e.run(actor_id="founder_p9_e2e")
    assert result["ok"] is True, result
    steps = {s["step"]: s for s in result["steps"]}
    for required in (
        "organization",
        "authentication_authorization",
        "workspace",
        "project",
        "prompt",
        "ai_generation",
        "asset_storage",
        "marketplace_publish",
        "purchase",
        "billing_invoice",
        "export_download",
        "phase9_ecosystem",
    ):
        assert steps[required]["ok"] is True, required


# =========================================================================
# Load & stress — 50 / 100 / 250 / 500 / 1000
# =========================================================================


def test_load_50_users():
    result = _svc().load.run_batch(50)
    assert result["ok"] is True
    assert result["failureRatePct"] == 0.0
    assert result["elapsedSec"] < 8.0


def test_load_100_users():
    result = _svc().load.run_batch(100)
    assert result["ok"] is True
    assert result["failureRatePct"] == 0.0
    assert result["elapsedSec"] < 12.0


def test_load_250_users():
    result = _svc().load.run_batch(250)
    assert result["ok"] is True
    assert result["failureRatePct"] == 0.0
    assert result["elapsedSec"] < 20.0


def test_stress_500_users():
    result = _svc().load.run_batch(500)
    assert result["ok"] is True
    assert result["failureRatePct"] == 0.0
    assert result["elapsedSec"] < 35.0
    assert result["opsPerSec"] > 10


def test_stress_1000_users():
    result = _svc().load.run_batch(1000)
    assert result["ok"] is True
    assert result["failureRatePct"] == 0.0
    assert result["elapsedSec"] < 60.0
    assert result["opsPerSec"] > 10


def test_recovery_after_load_spike():
    """System remains healthy after a large batch (recovery)."""
    spike = _svc().load.run_batch(100)
    assert spike["ok"] is True
    # Follow-up validation still works
    modules = _svc().modules.verify()
    assert modules["ok"] is True


# =========================================================================
# Security audit
# =========================================================================


def test_security_audit_full():
    result = _svc().security.audit()
    assert result["ok"] is True
    assert result["score"] == 100.0
    for check in _catalog().SECURITY_CHECKS:
        assert result["checks"][check] is True, check


def test_security_org_isolation_direct():
    ForbiddenError = _errors().ForbiddenError
    mt = _mt().get_multi_tenant_service()
    org_a = mt.create_organization(
        {"name": "A", "ownerId": "iso_a", "slug": f"isoa-{uuid.uuid4().hex[:6]}"}
    )["organization"]["id"]
    mt.create_organization(
        {"name": "B", "ownerId": "iso_b", "slug": f"isob-{uuid.uuid4().hex[:6]}"}
    )
    mr = sys.modules["app.services.marketplace_revenue.service"].get_marketplace_revenue_service()
    mr.revenue.record(
        {"organizationId": org_a, "stream": "marketplace", "amount": 10.0},
        actor_id="iso_a",
    )
    try:
        mr.revenue.report(actor_id="iso_b", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except ForbiddenError:
        pass


# =========================================================================
# API / database / production catalog
# =========================================================================


def test_production_endpoint_catalog():
    catalog = _svc().endpoints.catalog()
    assert catalog["ok"] is True
    paths = {e["path"] for e in catalog["endpoints"]}
    for required in (
        "/api/ready",
        "/api/router/status",
        "/api/video-engine/version",
        "/api/projects",
        "/api/assets",
        "/api/billing/plans",
        "/api/billing/subscription",
        "/api/marketplace",
        "/api/plugins",
        "/api/developers",
        "/api/automation",
        "/api/analytics",
        "/api/admin/system",
    ):
        assert required in paths


def test_database_validation_model_mapped():
    """Prisma Phase9ValidationRuns migration exists for production persistence."""
    migration = (
        ROOT.parent
        / "web"
        / "prisma"
        / "migrations"
        / "20260719_phase9_final_validation"
        / "migration.sql"
    )
    assert migration.exists()
    text = migration.read_text(encoding="utf-8")
    assert "Phase9ValidationRuns" in text


# =========================================================================
# Quality / full validation
# =========================================================================


def test_full_validation_quality_scores():
    result = _svc().full_validation(run_load=True, load_batches=(50, 100))
    assert result["ok"] is True
    assert result["phase9Complete"] is True
    assert result["marketplaceEcosystemVerified"] is True
    assert result["readyForPhase10"] is True
    q = result["quality"]
    assert q["enterpriseQualityScore"] >= 95.0
    assert q["securityScore"] >= 95.0
    assert q["performanceScore"] >= 95.0
    assert q["marketplaceScore"] >= 95.0
    assert q["developerPlatformScore"] >= 95.0
    assert q["scalabilityScore"] >= 95.0
    assert q["productionReadinessScore"] >= 95.0
    assert q["overall"] >= 95.0


def test_performance_summary_metrics():
    batch = _svc().load.run_batch(50)
    assert "metrics" in batch
    assert batch["metrics"]["apiLatency"] >= 0
    assert batch["metrics"]["marketplacePerformance"] == "ok"

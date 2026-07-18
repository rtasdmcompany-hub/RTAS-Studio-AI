"""Phase 7 Sprint 10 — Enterprise SaaS Platform final integration & validation tests."""

from __future__ import annotations

import importlib.util
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVC = ROOT / "app" / "services"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(name: str, path: Path):
    # Always re-exec so this suite owns a consistent in-memory store graph
    # even when earlier Phase 7 test modules reloaded the same packages.
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


def _wire(pkg: str, *attrs: str):
    target = sys.modules[pkg]
    svc = sys.modules[f"{pkg}.service"]
    for attr in attrs:
        setattr(target, attr, getattr(svc, attr))


def _bootstrap():
    _load_folder(
        "multi_tenant",
        ("version", "roles", "models", "validation", "store", "repository", "service", "engine"),
    )
    _wire("app.services.multi_tenant", "get_multi_tenant_service", "reset_engine")

    _load_folder(
        "enterprise_auth",
        (
            "version",
            "errors",
            "models",
            "store",
            "audit",
            "permission_engine",
            "sessions",
            "validators",
            "middleware",
            "sso",
            "service",
            "engine",
        ),
    )
    ea = sys.modules["app.services.enterprise_auth"]
    ea.get_enterprise_auth_service = sys.modules[
        "app.services.enterprise_auth.service"
    ].get_enterprise_auth_service
    ea.reset_engine = sys.modules["app.services.enterprise_auth.service"].reset_engine
    ea.require_access = sys.modules["app.services.enterprise_auth.middleware"].require_access

    _load_folder(
        "org_management",
        ("version", "models", "store", "security", "service", "engine"),
    )
    _wire("app.services.org_management", "get_org_management_service", "reset_engine")

    _load_folder(
        "project_collaboration",
        ("version", "roles", "models", "store", "permissions", "service", "engine"),
    )
    _wire(
        "app.services.project_collaboration",
        "get_project_collaboration_service",
        "reset_engine",
    )

    _load_folder(
        "asset_library",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    _wire("app.services.asset_library", "get_asset_library_service", "reset_engine")

    _load_folder(
        "enterprise_comms",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    _wire("app.services.enterprise_comms", "get_enterprise_comms_service", "reset_engine")

    _load_folder(
        "version_control",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    _wire("app.services.version_control", "get_version_control_service", "reset_engine")

    _load_folder(
        "analytics_bi",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    _wire("app.services.analytics_bi", "get_analytics_bi_service", "reset_engine")

    _load_folder(
        "platform_ops",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    _wire("app.services.platform_ops", "get_platform_ops_service", "reset_engine")

    _load_folder(
        "enterprise_saas",
        ("version", "catalog", "store", "service", "engine"),
    )
    es = sys.modules["app.services.enterprise_saas"]
    es.get_enterprise_saas_service = sys.modules[
        "app.services.enterprise_saas.service"
    ].get_enterprise_saas_service
    es.reset_engine = sys.modules["app.services.enterprise_saas.service"].reset_engine
    es.get_engine = sys.modules["app.services.enterprise_saas.service"].get_engine
    es.PHASE = sys.modules["app.services.enterprise_saas.version"].PHASE
    es.SPRINT = sys.modules["app.services.enterprise_saas.version"].SPRINT


_bootstrap()

version = sys.modules["app.services.enterprise_saas.version"]
catalog = sys.modules["app.services.enterprise_saas.catalog"]
service_mod = sys.modules["app.services.enterprise_saas.service"]
store = sys.modules["app.services.enterprise_saas.store"]


def setup_function():
    global version, catalog, service_mod, store
    # Re-bootstrap before every test so prior suites cannot leave dual stores.
    _bootstrap()
    version = sys.modules["app.services.enterprise_saas.version"]
    catalog = sys.modules["app.services.enterprise_saas.catalog"]
    service_mod = sys.modules["app.services.enterprise_saas.service"]
    store = sys.modules["app.services.enterprise_saas.store"]
    service_mod.reset_engine()


# --- Unit ---


def test_version_unit():
    assert version.PHASE == 7
    assert version.SPRINT == 10
    assert "Enterprise SaaS" in version.ENGINE_NAME
    assert version.QUALITY_THRESHOLD == 90.0
    assert version.STRESS_USER_BATCHES == (50, 100, 250, 500, 1000)


def test_catalog_unit():
    keys = {m["key"] for m in catalog.PHASE7_MODULES}
    assert keys == {
        "multi_tenant",
        "enterprise_auth",
        "org_management",
        "project_collaboration",
        "asset_library",
        "enterprise_comms",
        "version_control",
        "analytics_bi",
        "platform_ops",
    }
    assert "/api/ready" in catalog.PRODUCTION_ENDPOINTS
    assert "/api/enterprise/status" in catalog.PRODUCTION_ENDPOINTS


def test_status_unit():
    svc = service_mod.get_enterprise_saas_service()
    status = svc.status()
    assert status["ok"] is True
    assert status["sprint"] == 10
    assert status["phase"] == 7
    assert status["engines"]["verification"] == "ready"
    assert status["engines"]["e2e"] == "ready"
    assert status["engines"]["stress"] == "ready"
    assert status["engines"]["quality"] == "ready"
    assert len(status["modules"]) == 9


# --- Module verification ---


def test_all_phase7_modules_ready():
    svc = service_mod.get_enterprise_saas_service()
    result = svc.modules.verify_all()
    assert result["ok"] is True
    assert result["passed"] == result["total"] == 9
    assert all(m["ok"] for m in result["modules"])


# --- End-to-end ---


def test_end_to_end_saas_workflow():
    svc = service_mod.get_enterprise_saas_service()
    result = svc.e2e.run(actor_id=f"e2e_{uuid.uuid4().hex[:6]}")
    assert result["ok"] is True
    assert result["passed"] == result["total"]
    step_names = [s["step"] for s in result["steps"]]
    for required in (
        "organization",
        "workspace",
        "project",
        "prompt",
        "ai_engine",
        "workflow",
        "generation",
        "assets",
        "export",
        "download",
        "notifications",
        "activity",
        "comments",
        "version_control",
        "reviews",
        "approvals",
        "analytics",
        "reporting",
        "administration",
        "platform_operations",
    ):
        assert required in step_names, f"missing step: {required}"
    assert result["organizationId"]
    assert result["projectId"]
    assert result["assetId"]


# --- Stress ---


def test_stress_batches_50_to_1000():
    svc = service_mod.get_enterprise_saas_service()
    # Keep CI fast: full batch list with scaled large runs
    result = svc.stress.run_all((50, 100, 250, 500, 1000))
    assert result["ok"] is True
    assert result["maxUsers"] == 1000
    assert len(result["batches"]) == 5
    assert result["overallFailureRate"] <= 0.05
    for batch in result["batches"]:
        assert batch["ok"] is True
        assert "apiResponseTimeMs" in batch
        assert "memoryPeakMb" in batch
        assert "databasePerformanceMs" in batch
        assert "redisPerformanceMs" in batch
        assert "queuePerformanceMs" in batch
        assert "providerPerformanceMs" in batch
        assert "storagePerformanceMs" in batch
        assert batch["failureRate"] <= 0.05


def test_stress_batch_50_unit():
    svc = service_mod.get_enterprise_saas_service()
    batch = svc.stress.run_batch(50)
    assert batch["userCount"] == 50
    assert batch["ok"] is True
    assert batch["successes"] >= 48


# --- Quality scores ---


def test_quality_scores_production_ready():
    svc = service_mod.get_enterprise_saas_service()
    payload = svc.validate(
        run_stress=True,
        stress_batches=(50, 100),
        regression_pass_rate=1.0,
    )
    assert payload["ok"] is True
    scores = payload["scores"]
    assert scores["ok"] is True
    assert scores["enterpriseQualityScore"] >= 90.0
    assert scores["securityScore"] >= 90.0
    assert scores["performanceScore"] >= 70.0
    assert scores["scalabilityScore"] >= 70.0
    assert scores["productionReadinessScore"] >= 90.0


# --- Full validate ---


def test_full_platform_validate():
    svc = service_mod.get_enterprise_saas_service()
    payload = svc.validate(
        run_stress=True,
        stress_batches=(50, 100, 250, 500, 1000),
        regression_pass_rate=1.0,
    )
    assert payload["ok"] is True
    assert payload["modules"]["ok"] is True
    assert payload["e2e"]["ok"] is True
    assert payload["stress"]["ok"] is True
    assert payload["scores"]["ok"] is True
    obs = svc.observability()
    assert obs["ok"] is True
    assert obs["scores"]
    assert store.get_validation().get("ok") is True


# --- Security ---


def test_security_isolation_in_e2e_chain():
    """Owners can complete the SaaS chain; scores reflect auth/ops readiness."""
    svc = service_mod.get_enterprise_saas_service()
    modules = svc.modules.verify_all()
    e2e = svc.e2e.run(actor_id="sec_owner")
    scores = svc.quality.score(
        modules=modules, e2e=e2e, stress={"ok": True, "batches": [], "maxUsers": 0}, regression_pass_rate=1.0
    )
    assert e2e["ok"] is True
    assert scores["securityScore"] >= 96.0

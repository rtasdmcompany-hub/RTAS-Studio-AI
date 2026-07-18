"""Phase 7 Sprint 8 — Reporting, Analytics & Business Intelligence Engine tests."""

from __future__ import annotations

import importlib.util
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVC = ROOT / "app" / "services"

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


def _bootstrap():
    _load_folder(
        "multi_tenant",
        ("version", "roles", "models", "validation", "store", "repository", "service", "engine"),
    )
    mt = sys.modules["app.services.multi_tenant"]
    mt.get_multi_tenant_service = sys.modules["app.services.multi_tenant.service"].get_multi_tenant_service
    mt.reset_engine = sys.modules["app.services.multi_tenant.service"].reset_engine

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
        "analytics_bi",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    ab = sys.modules["app.services.analytics_bi"]
    ab.get_analytics_bi_service = sys.modules[
        "app.services.analytics_bi.service"
    ].get_analytics_bi_service
    ab.reset_engine = sys.modules["app.services.analytics_bi.service"].reset_engine
    ab.get_engine = sys.modules["app.services.analytics_bi.service"].get_engine


_bootstrap()

version = sys.modules["app.services.analytics_bi.version"]
catalog = sys.modules["app.services.analytics_bi.catalog"]
service_mod = sys.modules["app.services.analytics_bi.service"]
errors = sys.modules["app.services.enterprise_auth.errors"]
mt_service = sys.modules["app.services.multi_tenant.service"]


def setup_function():
    service_mod.reset_engine()


def _seed_org():
    mt = mt_service.get_multi_tenant_service()
    slug = f"bi-org-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "BI Org", "ownerId": "owner_1", "slug": slug}
    )
    org_id = created["organization"]["id"]
    ws_id = created["defaultWorkspace"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    mt.add_member({"organizationId": org_id, "userId": "viewer_1", "role": "viewer"})
    return org_id, ws_id


def _seed_metrics(svc, org_id, ws_id):
    svc.metrics.ingest(
        {
            "organizationId": org_id,
            "workspaceId": ws_id,
            "category": "ai",
            "metricKey": "jobs_created",
            "metricValue": 10,
        },
        actor_id="owner_1",
    )
    svc.metrics.ingest(
        {
            "organizationId": org_id,
            "category": "ai",
            "metricKey": "jobs_completed",
            "metricValue": 8,
        },
        actor_id="owner_1",
    )
    svc.metrics.ingest(
        {
            "organizationId": org_id,
            "category": "ai",
            "metricKey": "jobs_failed",
            "metricValue": 2,
        },
        actor_id="owner_1",
    )
    svc.metrics.record_usage(
        {
            "organizationId": org_id,
            "usageType": "storage",
            "count": 1,
            "bytes": 5 * 1024 * 1024 * 1024,
        }
    )
    svc.metrics.record_usage(
        {"organizationId": org_id, "usageType": "api", "count": 40}
    )
    svc.metrics.record_usage(
        {"organizationId": org_id, "usageType": "export", "count": 3}
    )
    svc.metrics.record_usage(
        {"organizationId": org_id, "usageType": "download", "count": 7}
    )
    svc.metrics.record_usage(
        {"organizationId": org_id, "usageType": "asset", "count": 12}
    )
    svc.metrics.ingest(
        {
            "organizationId": org_id,
            "category": "provider",
            "metricKey": "fal",
            "metricValue": 5,
        }
    )
    svc.metrics.ingest(
        {
            "organizationId": org_id,
            "category": "project",
            "metricKey": "active",
            "metricValue": 4,
        }
    )
    svc.metrics.record_performance(
        {
            "organizationId": org_id,
            "metricKey": "generation",
            "avgMs": 1200,
            "p95Ms": 2100,
            "successRate": 0.9,
            "sampleCount": 8,
        }
    )
    # map counters expected by overview
    st = sys.modules["app.services.analytics_bi.store"]
    st.bump(org_id, "ai.jobs_created", 10)
    st.bump(org_id, "ai.jobs_completed", 8)
    st.bump(org_id, "ai.jobs_failed", 2)
    st.bump(org_id, "active_users", 3)
    st.bump(org_id, "active_projects", 4)
    st.bump(org_id, "provider.fal", 5)
    st.bump(org_id, "queue.pending", 1)
    st.bump(org_id, "queue.throughput", 8)


# --- Unit ---


def test_version_unit():
    assert version.PHASE == 7
    assert version.SPRINT == 8
    assert "Business Intelligence" in version.ENGINE_NAME


def test_catalog_unit():
    assert "daily" in catalog.REPORT_TYPES
    assert catalog.normalize_report_type("ai") == "ai_usage"
    assert len(catalog.KPI_DEFS) >= 5


def test_status_unit():
    svc = service_mod.get_analytics_bi_service()
    status = svc.status()
    assert status["ok"] is True
    assert status["sprint"] == 8
    assert status["engines"]["analytics"] == "ready"
    assert status["engines"]["reporting"] == "ready"
    assert status["engines"]["bi"] == "ready"


# --- Analytics ---


def test_analytics_overview_and_slices():
    svc = service_mod.get_analytics_bi_service()
    org_id, ws_id = _seed_org()
    _seed_metrics(svc, org_id, ws_id)
    overview = svc.analytics.overview(actor_id="owner_1", organization_id=org_id)
    assert overview["ok"] is True
    assert overview["overview"]["aiJobsCreated"] >= 10
    assert overview["overview"]["aiJobsCompleted"] >= 8
    assert overview["overview"]["storageUsageBytes"] >= 0
    orgs = svc.analytics.organizations(actor_id="owner_1", organization_id=org_id)
    assert orgs["organizations"][0]["id"] == org_id
    projects = svc.analytics.projects(actor_id="owner_1", organization_id=org_id)
    assert projects["activeProjects"] >= 1
    ai = svc.analytics.ai(actor_id="owner_1", organization_id=org_id)
    assert ai["successRate"] > 0
    storage = svc.analytics.storage(actor_id="owner_1", organization_id=org_id, workspace_id=ws_id)
    assert storage["ok"] is True


# --- KPI / BI ---


def test_kpi_and_bi():
    svc = service_mod.get_analytics_bi_service()
    org_id, ws_id = _seed_org()
    _seed_metrics(svc, org_id, ws_id)
    kpis = svc.kpis.compute(actor_id="owner_1", organization_id=org_id)
    assert kpis["count"] >= 5
    keys = {k["kpiKey"] for k in kpis["kpis"]}
    assert "ai_success_rate" in keys
    bi = svc.bi.insights(actor_id="editor_1", organization_id=org_id, workspace_id=ws_id)
    assert bi["kpiDashboard"]
    assert bi["trendAnalysis"]
    assert bi["growthAnalysis"]
    assert bi["usageForecasting"]
    assert bi["costAnalysis"]
    assert bi["productivityAnalysis"]


# --- Reports ---


def test_report_generate_and_list():
    svc = service_mod.get_analytics_bi_service()
    org_id, _ = _seed_org()
    _seed_metrics(svc, org_id, None)
    for rtype in ["daily", "weekly", "ai_usage", "storage", "performance"]:
        gen = svc.reporting.generate(
            {"organizationId": org_id, "reportType": rtype, "title": f"{rtype} report"},
            actor_id="owner_1",
        )
        assert gen["report"]["reportType"] == rtype
        assert gen["report"]["status"] == "ready"
    listed = svc.reporting.list(actor_id="owner_1", organization_id=org_id)
    assert listed["count"] >= 5


# --- Security ---


def test_isolation_and_permissions_security():
    svc = service_mod.get_analytics_bi_service()
    org_id, ws_id = _seed_org()
    other = mt_service.get_multi_tenant_service().create_organization(
        {"name": "Other", "ownerId": "other_o", "slug": f"other-{uuid.uuid4().hex[:6]}"}
    )
    try:
        svc.analytics.overview(
            actor_id="owner_1", organization_id=other["organization"]["id"]
        )
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    try:
        svc.analytics.overview(
            actor_id="owner_1", organization_id=org_id, workspace_id="ws_fake"
        )
        assert False, "expected access denial"
    except (errors.ForbiddenError, errors.NotFoundError):
        pass
    # viewer can read overview
    overview = svc.analytics.overview(actor_id="viewer_1", organization_id=org_id)
    assert overview["ok"] is True
    # viewer cannot generate reports
    try:
        svc.reporting.generate(
            {"organizationId": org_id, "reportType": "daily"},
            actor_id="viewer_1",
        )
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    # editor can generate
    gen = svc.reporting.generate(
        {"organizationId": org_id, "workspaceId": ws_id, "reportType": "organization"},
        actor_id="editor_1",
    )
    assert gen["ok"] is True


def test_observability_and_performance():
    svc = service_mod.get_analytics_bi_service()
    org_id, _ = _seed_org()
    _seed_metrics(svc, org_id, None)
    start = time.perf_counter()
    for _ in range(10):
        svc.analytics.overview(actor_id="owner_1", organization_id=org_id)
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0
    obs = svc.observability()
    assert obs["apiPerformance"]["calls"] >= 1
    assert obs["errors"] == 0
    assert obs["cacheEfficiency"] >= 0

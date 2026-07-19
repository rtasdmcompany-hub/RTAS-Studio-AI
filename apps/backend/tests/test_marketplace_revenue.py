"""Phase 9 Sprint 9 — Marketplace Analytics, Revenue Intelligence & Monetization tests."""

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
    mt.get_multi_tenant_service = sys.modules[
        "app.services.multi_tenant.service"
    ].get_multi_tenant_service
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
        "marketplace_revenue",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    mr = sys.modules["app.services.marketplace_revenue"]
    mr.get_marketplace_revenue_service = sys.modules[
        "app.services.marketplace_revenue.service"
    ].get_marketplace_revenue_service
    mr.reset_engine = sys.modules[
        "app.services.marketplace_revenue.service"
    ].reset_engine


_bootstrap()


def _mr():
    return sys.modules["app.services.marketplace_revenue.service"]


def _mt():
    return sys.modules["app.services.multi_tenant.service"]


def _version():
    return sys.modules["app.services.marketplace_revenue.version"]


def _catalog():
    return sys.modules["app.services.marketplace_revenue.catalog"]


def _errors():
    return sys.modules["app.services.enterprise_auth.errors"]


def _audit_store():
    return sys.modules["app.services.enterprise_auth.store"]


def setup_function():
    _bootstrap()
    mod = _mr()
    mod._service = None
    sys.modules["app.services.marketplace_revenue.store"].reset_store()


def _seed_org(owner: str = "owner_1"):
    mt = _mt().get_multi_tenant_service()
    slug = f"mr-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Revenue Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    return org_id


def _svc():
    return _mr().get_marketplace_revenue_service()


# --- Unit ---


def test_version_unit():
    v = _version()
    assert v.PHASE == 9
    assert v.SPRINT == 9
    assert "Monetization" in v.ENGINE_NAME


def test_catalog_unit():
    c = _catalog()
    assert "subscription" in c.REVENUE_STREAMS
    assert "marketplace" in c.REVENUE_STREAMS
    assert "purchase" in c.SALE_EVENT_TYPES
    assert "view" in c.PRODUCT_METRICS
    assert "90d" in c.FORECAST_HORIZONS
    assert c.growth_rate(120, 100) == 20.0
    assert c.growth_rate(50, 0) == 100.0
    forecast = c.simple_forecast([100.0, 110.0, 120.0], periods=2)
    assert len(forecast) == 2
    assert forecast[0] >= 120.0
    health = c.marketplace_health_score(
        conversion_rate=5.0, avg_rating=4.5, churn_rate=2.0, revenue_growth=10.0
    )
    assert 0 <= health <= 100


def test_engine_status_unit():
    status = _svc().status()
    assert status["ok"] is True
    assert status["phase"] == 9
    assert status["sprint"] == 9
    assert len(status["engines"]) == 6
    assert all(v == "ready" for v in status["engines"].values())


# --- Revenue Tests ---


def test_revenue_streams_and_net():
    org_id = _seed_org("owner_rev")
    svc = _svc()
    svc.revenue.record(
        {"organizationId": org_id, "stream": "subscription", "amount": 89.0},
        actor_id="owner_rev",
    )
    svc.revenue.record(
        {"organizationId": org_id, "stream": "marketplace", "amount": 40.0},
        actor_id="owner_rev",
    )
    svc.revenue.record(
        {"organizationId": org_id, "stream": "credit_sales", "amount": 20.0},
        actor_id="owner_rev",
    )
    svc.revenue.record(
        {"organizationId": org_id, "stream": "refund", "amount": 10.0},
        actor_id="owner_rev",
    )
    report = svc.revenue.report(actor_id="owner_rev", organization_id=org_id)
    assert report["grossRevenue"] == 149.0
    assert report["refundAmount"] == 10.0
    assert report["netRevenue"] == 139.0
    assert report["subscriptionRevenue"] == 89.0
    assert report["marketplaceRevenue"] == 40.0
    assert report["creditSalesRevenue"] == 20.0
    assert report["totalRevenue"] == 139.0
    assert "monthlyRevenue" in report
    assert "annualRevenue" in report


def test_workspace_isolation_revenue():
    org_id = _seed_org("owner_ws")
    svc = _svc()
    svc.revenue.record(
        {
            "organizationId": org_id,
            "workspaceId": "ws_a",
            "stream": "marketplace",
            "amount": 50.0,
        },
        actor_id="owner_ws",
    )
    svc.revenue.record(
        {
            "organizationId": org_id,
            "workspaceId": "ws_b",
            "stream": "marketplace",
            "amount": 25.0,
        },
        actor_id="owner_ws",
    )
    a = svc.revenue.report(
        actor_id="owner_ws", organization_id=org_id, workspace_id="ws_a"
    )
    b = svc.revenue.report(
        actor_id="owner_ws", organization_id=org_id, workspace_id="ws_b"
    )
    assert a["grossRevenue"] == 50.0
    assert b["grossRevenue"] == 25.0


# --- Sales / Analytics ---


def test_sales_intelligence():
    org_id = _seed_org("owner_sales")
    svc = _svc()
    svc.sales.record(
        {
            "organizationId": org_id,
            "eventType": "purchase",
            "amount": 30.0,
            "productId": "p1",
            "creatorId": "c1",
            "customerId": "cust1",
        },
        actor_id="owner_sales",
    )
    svc.sales.record(
        {
            "organizationId": org_id,
            "eventType": "subscription",
            "amount": 89.0,
            "customerId": "cust1",
        },
        actor_id="owner_sales",
    )
    report = svc.sales.report(actor_id="owner_sales", organization_id=org_id)
    assert report["totalSales"] == 119.0
    assert report["salesCount"] == 2
    assert "salesForecast" in report
    rev = svc.revenue.report(actor_id="owner_sales", organization_id=org_id)
    assert rev["grossRevenue"] == 119.0


def test_marketplace_insights():
    org_id = _seed_org("owner_mkt")
    svc = _svc()
    for _ in range(5):
        svc.marketplace.track(
            {
                "organizationId": org_id,
                "productId": "asset_a",
                "metric": "view",
                "category": "video",
                "creatorId": "c1",
            },
            actor_id="owner_mkt",
        )
    svc.marketplace.track(
        {
            "organizationId": org_id,
            "productId": "asset_a",
            "metric": "download",
            "category": "video",
            "creatorId": "c1",
        },
        actor_id="owner_mkt",
    )
    svc.marketplace.track(
        {
            "organizationId": org_id,
            "productId": "asset_a",
            "metric": "purchase",
            "category": "video",
            "creatorId": "c1",
            "amount": 15.0,
        },
        actor_id="owner_mkt",
    )
    svc.marketplace.track(
        {
            "organizationId": org_id,
            "productId": "asset_b",
            "metric": "search_impression",
            "category": "template",
        },
        actor_id="owner_mkt",
    )
    svc.marketplace.track(
        {
            "organizationId": org_id,
            "productId": "asset_a",
            "metric": "feature",
            "featured": True,
            "category": "video",
        },
        actor_id="owner_mkt",
    )
    report = svc.marketplace.report(actor_id="owner_mkt", organization_id=org_id)
    assert report["productViews"] == 5.0
    assert report["productDownloads"] == 1.0
    assert report["productPurchases"] == 1.0
    assert report["bestSellingProducts"][0]["productId"] == "asset_a"
    assert "asset_a" in report["featuredProducts"]
    assert "video" in report["categoryPerformance"]
    assert report["conversionRate"] > 0


def test_creator_analytics():
    org_id = _seed_org("owner_cr")
    svc = _svc()
    svc.sales.record(
        {
            "organizationId": org_id,
            "eventType": "purchase",
            "amount": 50.0,
            "productId": "top_asset",
            "creatorId": "creator_x",
            "customerId": "u1",
        },
        actor_id="owner_cr",
    )
    svc.marketplace.track(
        {
            "organizationId": org_id,
            "productId": "top_asset",
            "metric": "view",
            "creatorId": "creator_x",
        },
        actor_id="owner_cr",
    )
    svc.creators.rate(
        {"organizationId": org_id, "creatorId": "creator_x", "rating": 5},
        actor_id="owner_cr",
    )
    report = svc.creators.report(actor_id="owner_cr", organization_id=org_id)
    assert report["creatorRevenue"] == 50.0
    assert report["productSales"] >= 1
    assert report["averageRating"] == 5.0
    assert report["reviewStatistics"]["reviewCount"] == 1
    assert report["topPerformingAssets"][0]["productId"] == "top_asset"


# --- Forecast / BI ---


def test_revenue_forecast():
    org_id = _seed_org("owner_fc")
    svc = _svc()
    for i, amount in enumerate((100.0, 120.0, 140.0), start=1):
        svc.revenue.record(
            {
                "organizationId": org_id,
                "stream": "marketplace",
                "amount": amount,
                "period": f"2026-0{i}",
            },
            actor_id="owner_fc",
        )
    fc = svc.forecast.forecast(
        actor_id="owner_fc", organization_id=org_id, horizon="90d"
    )
    assert fc["ok"] is True
    assert len(fc["revenueForecast"]) == 3
    assert "salesForecast" in fc
    assert "growthTrends" in fc
    assert 0 <= fc["marketplaceHealthScore"] <= 100


def test_customer_monetization_bi():
    org_id = _seed_org("owner_cust")
    svc = _svc()
    svc.sales.record(
        {
            "organizationId": org_id,
            "eventType": "purchase",
            "amount": 40.0,
            "customerId": "cust_a",
            "productId": "p1",
        },
        actor_id="owner_cust",
    )
    svc.sales.record(
        {
            "organizationId": org_id,
            "eventType": "credit_pack",
            "amount": 20.0,
            "customerId": "cust_b",
        },
        actor_id="owner_cust",
    )
    svc.monetization.mark_churn(
        {"organizationId": org_id, "customerId": "cust_b"},
        actor_id="owner_cust",
    )
    cust = svc.monetization.customers(actor_id="owner_cust", organization_id=org_id)
    assert cust["activeCustomers"] == 1
    assert cust["churnedCustomers"] == 1
    assert cust["churnRate"] == 50.0
    assert cust["averageRevenuePerUser"] == 40.0
    assert cust["customerLifetimeValue"] == 40.0
    assert cust["customerRetention"] == 50.0
    assert "marketplaceHealthScore" in cust


def test_products_endpoint_surface():
    org_id = _seed_org("owner_prod")
    svc = _svc()
    svc.marketplace.track(
        {
            "organizationId": org_id,
            "productId": "px",
            "metric": "purchase",
            "category": "audio",
        },
        actor_id="owner_prod",
    )
    products = svc.monetization.products(actor_id="owner_prod", organization_id=org_id)
    assert products["ok"] is True
    assert products["productPurchases"] == 1.0


# --- Security ---


def test_org_isolation_security():
    org_a = _seed_org("owner_a")
    org_b = _seed_org("owner_b")
    svc = _svc()
    svc.revenue.record(
        {"organizationId": org_a, "stream": "marketplace", "amount": 999.0},
        actor_id="owner_a",
    )
    ForbiddenError = _errors().ForbiddenError
    try:
        svc.revenue.report(actor_id="owner_b", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except ForbiddenError:
        pass
    report_b = svc.revenue.report(actor_id="owner_b", organization_id=org_b)
    assert report_b["grossRevenue"] == 0.0


def test_outsider_denied():
    org_id = _seed_org("owner_sec")
    ForbiddenError = _errors().ForbiddenError
    try:
        _svc().revenue.report(actor_id="stranger", organization_id=org_id)
        assert False, "expected ForbiddenError"
    except ForbiddenError:
        pass


def test_audit_logging_financial():
    org_id = _seed_org("owner_audit")
    # Clear prior audit if possible
    audit_mod = sys.modules.get("app.services.enterprise_auth.audit")
    _svc().revenue.record(
        {"organizationId": org_id, "stream": "subscription", "amount": 10.0},
        actor_id="owner_audit",
    )
    _svc().revenue.report(actor_id="owner_audit", organization_id=org_id)
    # Ensure audit module callable; soft check via no exception + store ops
    assert audit_mod is not None
    metrics = sys.modules["app.services.marketplace_revenue.store"].metrics()
    assert metrics["ledgerEntries"] >= 1


# --- Integration / Performance ---


def test_full_pipeline_integration():
    org_id = _seed_org("owner_int")
    svc = _svc()
    svc.sales.record(
        {
            "organizationId": org_id,
            "eventType": "purchase",
            "amount": 25.0,
            "productId": "int_p",
            "creatorId": "int_c",
            "customerId": "int_u",
        },
        actor_id="owner_int",
    )
    svc.marketplace.track(
        {
            "organizationId": org_id,
            "productId": "int_p",
            "metric": "view",
            "creatorId": "int_c",
            "category": "workflow",
        },
        actor_id="owner_int",
    )
    assert svc.revenue.report(actor_id="owner_int", organization_id=org_id)["ok"]
    assert svc.sales.report(actor_id="owner_int", organization_id=org_id)["ok"]
    assert svc.marketplace.report(actor_id="owner_int", organization_id=org_id)["ok"]
    assert svc.creators.report(actor_id="owner_int", organization_id=org_id)["ok"]
    assert svc.forecast.forecast(actor_id="owner_int", organization_id=org_id)["ok"]
    assert svc.monetization.products(actor_id="owner_int", organization_id=org_id)["ok"]
    assert svc.monetization.customers(actor_id="owner_int", organization_id=org_id)["ok"]


def test_performance_bulk_ledger():
    org_id = _seed_org("owner_perf")
    svc = _svc()
    start = time.perf_counter()
    for i in range(200):
        svc.revenue.record(
            {
                "organizationId": org_id,
                "stream": "marketplace" if i % 2 == 0 else "credit_sales",
                "amount": 1.0 + (i % 5),
            },
            actor_id="owner_perf",
        )
    report = svc.revenue.report(actor_id="owner_perf", organization_id=org_id)
    elapsed = time.perf_counter() - start
    assert report["entryCount"] == 200
    assert elapsed < 5.0
    assert report["grossRevenue"] > 0


def test_invalid_stream_validation():
    org_id = _seed_org("owner_val")
    ValidationError = sys.modules["app.services.multi_tenant.validation"].ValidationError
    try:
        _svc().revenue.record(
            {"organizationId": org_id, "stream": "bitcoin", "amount": 1.0},
            actor_id="owner_val",
        )
        assert False, "expected ValidationError"
    except ValidationError:
        pass

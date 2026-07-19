"""Phase 8 Sprint 8 — Usage Analytics, Cost Optimization & AI Provider Billing tests."""

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
        "provider_analytics",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    pa = sys.modules["app.services.provider_analytics"]
    pa.get_provider_analytics_service = sys.modules[
        "app.services.provider_analytics.service"
    ].get_provider_analytics_service
    pa.reset_engine = sys.modules["app.services.provider_analytics.service"].reset_engine


_bootstrap()


def _pa():
    return sys.modules["app.services.provider_analytics.service"]


def _mt():
    return sys.modules["app.services.multi_tenant.service"]


def _version():
    return sys.modules["app.services.provider_analytics.version"]


def _catalog():
    return sys.modules["app.services.provider_analytics.catalog"]


def _errors():
    return sys.modules["app.services.enterprise_auth.errors"]


def _validation():
    return sys.modules["app.services.multi_tenant.validation"]


def setup_function():
    _bootstrap()
    mod = _pa()
    mod._service = None
    sys.modules["app.services.provider_analytics.store"].reset_store()


def _seed_org(owner: str = "owner_1"):
    mt = _mt().get_multi_tenant_service()
    slug = f"pa-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Analytics Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    return org_id


def _svc():
    return _pa().get_provider_analytics_service()


# --- Unit ---


def test_version_unit():
    v = _version()
    assert v.PHASE == 8
    assert v.SPRINT == 8
    assert "Usage Analytics" in v.ENGINE_NAME
    assert "Provider Billing" in v.ENGINE_NAME


def test_catalog_unit():
    c = _catalog()
    for provider in ("openai", "fal", "runpod", "gemini", "anthropic"):
        profile = c.provider_profile(provider)
        assert profile is not None
        assert profile["costPerRequestUsd"] > 0
        assert profile["qualityScore"] > 0
    assert c.provider_profile("unknown") is None
    assert c.COST_COMPONENTS == ("provider", "gpu", "api", "storage", "bandwidth", "rendering")
    assert c.BUDGET_ALERT_THRESHOLDS == (0.5, 0.8, 0.95)


def test_status_unit():
    status = _svc().status()
    assert status["ok"] is True
    assert status["sprint"] == 8
    for engine in (
        "usageAnalytics",
        "providerCostTracking",
        "internalBilling",
        "costOptimization",
        "budgetControl",
        "profitAnalytics",
    ):
        assert status["engines"][engine] == "ready"
    assert "openai" in status["providers"]


# --- Cost calculation ---


def test_cost_calculation():
    svc = _svc()
    breakdown = svc.costs.calculate_cost("openai")
    assert breakdown["provider"] == 0.045
    for component in ("gpu", "api", "storage", "bandwidth", "rendering"):
        assert breakdown[component] > 0
    assert abs(breakdown["total"] - sum(v for k, v in breakdown.items() if k != "total")) < 1e-9

    no_render = svc.costs.calculate_cost("fal", include_rendering=False)
    assert no_render["rendering"] == 0.0

    double = svc.costs.calculate_cost("openai", units=2.0)
    assert abs(double["provider"] - 0.09) < 1e-9

    try:
        svc.costs.calculate_cost("nonexistent")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_register_future_provider():
    org_id = _seed_org("owner_fp")
    svc = _svc()
    result = svc.costs.register_provider(
        "mistral",
        {
            "label": "Mistral AI",
            "costPerRequestUsd": 0.015,
            "avgLatencyMs": 1200.0,
            "qualityScore": 8.5,
            "capabilities": ["text"],
        },
        actor_id="owner_fp",
    )
    assert result["ok"] is True
    assert "mistral" in svc.costs.providers()
    breakdown = svc.costs.calculate_cost("mistral")
    assert breakdown["provider"] == 0.015

    # It participates in recommendations
    rec = svc.optimizer.recommendations(
        actor_id="owner_fp", organization_id=org_id, mode="lowest_cost", capability="text"
    )
    assert rec["recommended"]["provider"] == "mistral"


# --- Usage analytics ---


def test_usage_analytics_dimensions():
    org_id = _seed_org("owner_ua")
    svc = _svc()
    for i in range(6):
        svc.analytics.record(
            org_id,
            "openai",
            model="gpt-5",
            user_id=f"user_{i % 2}",
            workspace_id="ws_a",
            status="success",
            latency_ms=2000 + i,
            credits_charged=2.0,
        )
    for _ in range(2):
        svc.analytics.record(
            org_id, "fal", model="flux-pro", user_id="user_0",
            workspace_id="ws_b", status="failed", credits_charged=0.0,
        )

    usage = svc.analytics.usage(actor_id="owner_ua", organization_id=org_id)
    assert usage["totals"]["requests"] == 8
    assert usage["totals"]["successful"] == 6
    assert usage["totals"]["failed"] == 2
    assert usage["totals"]["successRatePct"] == 75.0
    assert usage["periods"]["daily"] == 8
    assert usage["periods"]["weekly"] == 8
    assert usage["periods"]["monthly"] == 8
    assert usage["byUser"]["user_0"]["requests"] == 5
    assert usage["byUser"]["user_1"]["requests"] == 3
    assert usage["byWorkspace"]["ws_a"]["requests"] == 6
    assert usage["byProvider"]["openai"]["successful"] == 6
    assert usage["byProvider"]["fal"]["failed"] == 2
    assert usage["byModel"]["gpt-5"]["requests"] == 6


def test_provider_analytics_report():
    org_id = _seed_org("owner_pr")
    svc = _svc()
    svc.analytics.record(org_id, "anthropic", latency_ms=2100.0, credits_charged=3.0)
    svc.analytics.record(org_id, "anthropic", latency_ms=1900.0, credits_charged=3.0)
    report = svc.analytics.provider_analytics(actor_id="owner_pr", organization_id=org_id)
    anthropic = report["providers"]["anthropic"]
    assert anthropic["requests"] == 2
    assert anthropic["avgLatencyMs"] == 2000.0
    assert anthropic["revenueUsd"] == 0.3  # 6 credits * 0.05
    assert report["providers"]["openai"]["requests"] == 0


# --- Internal billing ---


def test_cost_and_revenue_aggregation():
    org_id = _seed_org("owner_cb")
    svc = _svc()
    for _ in range(10):
        svc.analytics.record(org_id, "runpod", credits_charged=1.0)

    costs = svc.billing.costs(actor_id="owner_cb", organization_id=org_id)
    assert costs["generations"] == 10
    assert costs["components"]["provider"] == 0.17  # 10 * 0.017
    assert costs["totalCostUsd"] > costs["components"]["provider"]
    assert abs(costs["costPerGenerationUsd"] - costs["totalCostUsd"] / 10) < 1e-6
    assert costs["monthlyOperatingCostUsd"] > _catalog().MONTHLY_FIXED_OVERHEAD_USD

    revenue = svc.billing.revenue(actor_id="owner_cb", organization_id=org_id)
    assert revenue["creditsBilled"] == 10.0
    assert revenue["revenueUsd"] == 0.5
    assert revenue["monthlyRevenueUsd"] == 0.5


# --- Budget management ---


def test_budget_update_and_get():
    org_id = _seed_org("owner_bu")
    svc = _svc()
    updated = svc.budgets.update(
        {
            "organizationId": org_id,
            "dailyLimitUsd": 10.0,
            "monthlyLimitUsd": 200.0,
            "hardStop": True,
        },
        actor_id="owner_bu",
    )
    assert updated["budget"]["dailyLimitUsd"] == 10.0
    assert updated["budget"]["hardStop"] is True

    ws_budget = svc.budgets.update(
        {
            "organizationId": org_id,
            "scope": "workspace",
            "scopeId": "ws_1",
            "dailyLimitUsd": 2.0,
        },
        actor_id="owner_bu",
    )
    assert ws_budget["budget"]["scope"] == "workspace"

    result = svc.budgets.get(actor_id="owner_bu", organization_id=org_id)
    assert result["budget"]["monthlyLimitUsd"] == 200.0
    assert len(result["workspaceBudgets"]) == 1
    assert any(e["eventType"] == "budget_updated" for e in result["recentEvents"])

    # Negative limits rejected
    try:
        svc.budgets.update(
            {"organizationId": org_id, "dailyLimitUsd": -5}, actor_id="owner_bu"
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_budget_alerts_and_hard_stop():
    org_id = _seed_org("owner_ba")
    svc = _svc()
    svc.budgets.update(
        {"organizationId": org_id, "dailyLimitUsd": 1.0, "hardStop": True},
        actor_id="owner_ba",
    )
    # Spend ~0.60 USD (openai total ≈ 0.0597/request * 10)
    for _ in range(10):
        svc.analytics.record(org_id, "openai", credits_charged=1.0)

    check = svc.budgets.check_spend(org_id, additional_cost_usd=0.0)
    assert check["allowed"] is True
    assert check["spending"]["dailySpentUsd"] > 0.5

    # Crossing 80% threshold triggers an alert
    check2 = svc.budgets.check_spend(org_id, additional_cost_usd=0.25)
    assert any(a["eventType"] == "threshold_alert" for a in check2["alerts"])

    # Exceeding the limit with hard stop blocks spending
    check3 = svc.budgets.check_spend(org_id, additional_cost_usd=1.0)
    assert check3["allowed"] is False
    assert "limit reached" in check3["reason"]
    assert any(a["eventType"] == "limit_reached" for a in check3["alerts"])

    # Soft budget (no hard stop) alerts but allows
    svc.budgets.update(
        {"organizationId": org_id, "dailyLimitUsd": 1.0, "hardStop": False},
        actor_id="owner_ba",
    )
    check4 = svc.budgets.check_spend(org_id, additional_cost_usd=1.0)
    assert check4["allowed"] is True


# --- Optimization ---


def test_optimization_modes():
    org_id = _seed_org("owner_om")
    svc = _svc()

    lowest = svc.optimizer.recommendations(
        actor_id="owner_om", organization_id=org_id, mode="lowest_cost"
    )
    assert lowest["recommended"]["provider"] == "runpod"  # cheapest at 0.017
    assert lowest["failoverOrder"][0] == "runpod"
    assert len(lowest["failoverOrder"]) == 5

    fastest = svc.optimizer.recommendations(
        actor_id="owner_om", organization_id=org_id, mode="fastest"
    )
    assert fastest["recommended"]["provider"] == "fal"  # 1500ms

    quality = svc.optimizer.recommendations(
        actor_id="owner_om", organization_id=org_id, mode="best_quality"
    )
    assert quality["recommended"]["provider"] == "anthropic"  # 9.5

    text_only = svc.optimizer.recommendations(
        actor_id="owner_om", organization_id=org_id, mode="lowest_cost", capability="text"
    )
    assert text_only["recommended"]["provider"] == "gemini"  # cheapest text provider
    assert all(
        p in ("openai", "gemini", "anthropic") for p in text_only["failoverOrder"]
    )

    try:
        svc.optimizer.recommendations(
            actor_id="owner_om", organization_id=org_id, mode="cheapest_ever"
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass

    history = svc.optimizer.history(actor_id="owner_om", organization_id=org_id)
    assert history["count"] == 4


def test_cost_saving_opportunities():
    org_id = _seed_org("owner_cs")
    svc = _svc()
    for _ in range(20):
        svc.analytics.record(org_id, "openai", credits_charged=1.0)
    rec = svc.optimizer.recommendations(
        actor_id="owner_cs", organization_id=org_id, mode="lowest_cost"
    )
    opportunities = rec["costSavingOpportunities"]
    assert len(opportunities) == 1
    opp = opportunities[0]
    assert opp["fromProvider"] == "openai"
    assert opp["toProvider"] == "runpod"
    assert opp["requests"] == 20
    assert abs(opp["potentialSavingsUsd"] - (0.045 - 0.017) * 20) < 1e-6


# --- Profit analytics ---


def test_profit_analytics():
    org_id = _seed_org("owner_pf")
    svc = _svc()
    # 100 generations on fal at 3 credits each: revenue = 300 * 0.05 = 15 USD
    for _ in range(100):
        svc.analytics.record(org_id, "fal", credits_charged=3.0)

    result = svc.profit.profit(actor_id="owner_pf", organization_id=org_id)
    profit = result["profit"]
    assert profit["revenueUsd"] == 15.0
    assert abs(profit["providerCostUsd"] - 2.1) < 1e-6  # 100 * 0.021
    assert profit["grossProfitUsd"] == profit["revenueUsd"] - profit["providerCostUsd"]
    assert (
        abs(
            profit["netProfitUsd"]
            - (
                profit["grossProfitUsd"]
                - profit["infrastructureCostUsd"]
                - profit["fixedOverheadUsd"]
            )
        )
        < 1e-6
    )
    assert profit["marginPct"] == 86.0  # (15 - 2.1) / 15
    assert len(result["reports"]) == 1


# --- Security ---


def test_org_isolation_and_financial_protection():
    org_a = _seed_org("owner_sa")
    org_b = _seed_org("owner_sb")
    svc = _svc()
    svc.analytics.record(org_a, "openai", credits_charged=5.0)

    # Non-member cannot read financial data
    for call in (
        lambda: svc.analytics.usage(actor_id="owner_sb", organization_id=org_a),
        lambda: svc.billing.costs(actor_id="owner_sb", organization_id=org_a),
        lambda: svc.billing.revenue(actor_id="owner_sb", organization_id=org_a),
        lambda: svc.profit.profit(actor_id="owner_sb", organization_id=org_a),
        lambda: svc.budgets.get(actor_id="owner_sb", organization_id=org_a),
    ):
        try:
            call()
            assert False, "expected ForbiddenError"
        except _errors().ForbiddenError:
            pass

    # Editor cannot update budgets (manage permission required)
    try:
        svc.budgets.update(
            {"organizationId": org_b, "dailyLimitUsd": 1.0}, actor_id="editor_1"
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass

    # Usage from org A never leaks into org B analytics
    usage_b = svc.analytics.usage(actor_id="owner_sb", organization_id=org_b)
    assert usage_b["totals"]["requests"] == 0


def test_workspace_isolation_in_budgets():
    org_id = _seed_org("owner_wi")
    svc = _svc()
    svc.budgets.update(
        {
            "organizationId": org_id,
            "scope": "workspace",
            "scopeId": "ws_x",
            "dailyLimitUsd": 0.1,
            "hardStop": True,
        },
        actor_id="owner_wi",
    )
    # Spend in a different workspace does not count against ws_x
    for _ in range(10):
        svc.analytics.record(org_id, "openai", workspace_id="ws_other", credits_charged=1.0)
    check = svc.budgets.check_spend(org_id, workspace_id="ws_x")
    assert check["allowed"] is True
    assert check["spending"]["dailySpentUsd"] == 0.0

    # Spend inside ws_x hits its own limit
    for _ in range(3):
        svc.analytics.record(org_id, "openai", workspace_id="ws_x", credits_charged=1.0)
    check2 = svc.budgets.check_spend(org_id, workspace_id="ws_x", additional_cost_usd=0.05)
    assert check2["allowed"] is False


# --- Performance ---


def test_performance_bulk_analytics():
    org_id = _seed_org("owner_perf")
    svc = _svc()
    providers = ["openai", "fal", "runpod", "gemini", "anthropic"]
    start = time.perf_counter()
    for i in range(1000):
        svc.analytics.record(
            org_id,
            providers[i % 5],
            model=f"model_{i % 3}",
            user_id=f"user_{i % 10}",
            workspace_id=f"ws_{i % 4}",
            status="success" if i % 10 else "failed",
            credits_charged=1.0,
        )
    usage = svc.analytics.usage(actor_id="owner_perf", organization_id=org_id)
    costs = svc.billing.costs(actor_id="owner_perf", organization_id=org_id)
    elapsed = time.perf_counter() - start
    assert elapsed < 10.0
    assert usage["totals"]["requests"] == 1000
    assert usage["totals"]["failed"] == 100
    assert len(usage["byUser"]) == 10
    assert len(usage["byWorkspace"]) == 4
    assert costs["generations"] == 1000
    metrics = sys.modules["app.services.provider_analytics.store"].metrics()
    assert metrics["errorCount"] == 0

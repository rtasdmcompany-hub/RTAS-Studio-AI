"""Phase 8 Sprint 4 — Credit Consumption, Usage Metering & Quota tests."""

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
        "billing",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    bil = sys.modules["app.services.billing"]
    bil.get_billing_service = sys.modules["app.services.billing.service"].get_billing_service
    bil.reset_engine = sys.modules["app.services.billing.service"].reset_engine

    _load_folder(
        "payment_processing",
        ("version", "catalog", "models", "store", "signatures", "service", "engine"),
    )
    pp = sys.modules["app.services.payment_processing"]
    pp.get_payment_processing_service = sys.modules[
        "app.services.payment_processing.service"
    ].get_payment_processing_service
    pp.reset_engine = sys.modules["app.services.payment_processing.service"].reset_engine

    _load_folder(
        "credit_metering",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    cm = sys.modules["app.services.credit_metering"]
    cm.get_credit_metering_service = sys.modules[
        "app.services.credit_metering.service"
    ].get_credit_metering_service
    cm.reset_engine = sys.modules["app.services.credit_metering.service"].reset_engine


_bootstrap()

def _cm():
    return sys.modules["app.services.credit_metering.service"]


def _pp():
    return sys.modules["app.services.payment_processing.service"]


def _mt():
    return sys.modules["app.services.multi_tenant.service"]


def _version():
    return sys.modules["app.services.credit_metering.version"]


def _catalog():
    return sys.modules["app.services.credit_metering.catalog"]


def _errors():
    return sys.modules["app.services.enterprise_auth.errors"]


def _validation():
    return sys.modules["app.services.multi_tenant.validation"]


def setup_function():
    # Sibling Phase 8 tests reload importlib packages; re-bind a consistent stack.
    _bootstrap()
    sys.modules["app.services.payment_processing.service"].reset_engine()
    mod = sys.modules["app.services.credit_metering.service"]
    mod._service = None
    sys.modules["app.services.credit_metering.store"].reset_store()


def _seed_org(owner: str = "owner_1", credits: int = 500):
    mt = _mt().get_multi_tenant_service()
    slug = f"cm-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Meter Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    if credits > 0:
        pp = _pp().get_payment_processing_service()
        pp.transactions.credit(
            org_id,
            credits,
            txn_type="adjustment",
            credit_category="purchased",
            actor_id=owner,
            reason="test_seed",
        )
    return org_id


# --- Unit ---


def test_version_unit():
    version = _version()
    assert version.PHASE == 8
    assert version.SPRINT == 4
    assert "Quota" in version.ENGINE_NAME


def test_catalog_unit():
    catalog = _catalog()
    assert catalog.credits_for_service("image_generation") == 5
    assert catalog.credits_for_service("video") == 40
    assert catalog.normalize_service("bg_remove") == "background_removal"
    assert catalog.plan_quota("enterprise")["unlimited"] is True
    assert catalog.provider_rate("fal") > 0


def test_status_unit():
    svc = _cm().get_credit_metering_service()
    status = svc.status()
    assert status["ok"] is True
    assert status["sprint"] == 4
    assert status["engines"]["consumption"] == "ready"
    assert status["engines"]["quotaManager"] == "ready"
    assert "image_generation" in status["serviceTypes"]


# --- Credit / Cost ---


def test_cost_estimate():
    svc = _cm().get_credit_metering_service()
    org_id = _seed_org(credits=0)
    est = svc.costs.estimate(
        organization_id=org_id,
        service_type="video_generation",
        provider="runway",
        quantity=1,
    )
    assert est["ok"] is True
    assert est["estimate"]["credits"] == 40
    assert est["estimate"]["providerCostUsd"] > 0
    assert est["estimate"]["gpuCostUsd"] > 0
    assert "estimatedProfitMarginUsd" in est["estimate"]
    assert est["estimate"]["monthlyOperatingCostUsd"] > 0


def test_consume_and_usage_metering():
    svc = _cm().get_credit_metering_service()
    org_id = _seed_org("owner_c", credits=200)
    result = svc.consumption.consume(
        {
            "organizationId": org_id,
            "serviceType": "image_generation",
            "provider": "fal",
            "quantity": 2,
        },
        actor_id="owner_c",
    )
    assert result["ok"] is True
    assert result["usage"]["credits"] == 10
    assert result["creditsRemaining"] == 190

    usage = svc.consumption.usage_summary(actor_id="owner_c", organization_id=org_id)
    assert usage["creditsUsed"]["daily"] == 10
    assert usage["creditsUsed"]["monthly"] == 10
    assert usage["creditsRemaining"] == 190

    hist = svc.consumption.history(actor_id="owner_c", organization_id=org_id)
    assert hist["count"] == 1
    assert hist["usage"][0]["serviceType"] == "image_generation"


def test_quota_enforcement():
    svc = _cm().get_credit_metering_service()
    org_id = _seed_org("owner_q", credits=1000)
    # Tight daily quota
    q = svc.quotas.ensure(org_id)
    q.daily_limit = 15
    q.monthly_limit = 1000
    q.unlimited = False
    sys.modules["app.services.credit_metering.store"].save_quota(q)

    svc.consumption.consume(
        {"organizationId": org_id, "serviceType": "image_generation", "credits": 10},
        actor_id="owner_q",
    )
    try:
        svc.consumption.consume(
            {"organizationId": org_id, "serviceType": "image_generation", "credits": 10},
            actor_id="owner_q",
        )
        assert False, "expected daily quota ValidationError"
    except _validation().ValidationError as exc:
        assert "daily" in str(exc).lower()


def test_enterprise_unlimited():
    svc = _cm().get_credit_metering_service()
    org_id = _seed_org("owner_e", credits=50)
    q = svc.quotas.ensure(org_id, plan_key="enterprise")
    assert q.unlimited is True
    # Consume more than typical daily without quota failure (only wallet limits)
    result = svc.consumption.consume(
        {"organizationId": org_id, "serviceType": "audio_generation", "credits": 40},
        actor_id="owner_e",
    )
    assert result["ok"] is True
    assert result["fairUsage"]["level"] == "unlimited"


def test_analytics_and_providers():
    svc = _cm().get_credit_metering_service()
    org_id = _seed_org("owner_a", credits=300)
    svc.quotas.ensure(org_id, plan_key="professional")
    for service, provider in (
        ("image_generation", "fal"),
        ("video_generation", "runway"),
        ("voice_cloning", "replicate"),
    ):
        svc.consumption.consume(
            {
                "organizationId": org_id,
                "serviceType": service,
                "provider": provider,
            },
            actor_id="owner_a",
        )
    analytics = svc.analytics.analytics(actor_id="owner_a", organization_id=org_id)
    assert analytics["totals"]["requestCount"] == 3
    assert analytics["byService"]["image_generation"] == 5
    assert analytics["byService"]["video_generation"] == 40
    assert analytics["byProvider"]["fal"] == 5
    assert analytics["totals"]["operatingCostUsd"] > 0


def test_insufficient_credits():
    svc = _cm().get_credit_metering_service()
    org_id = _seed_org("owner_i", credits=3)
    try:
        svc.consumption.consume(
            {"organizationId": org_id, "serviceType": "image_generation"},
            actor_id="owner_i",
        )
        assert False, "expected insufficient credits"
    except _validation().ValidationError as exc:
        assert "insufficient" in str(exc).lower()


def test_ownership_isolation():
    svc = _cm().get_credit_metering_service()
    org_a = _seed_org("owner_a2", credits=100)
    org_b = _seed_org("owner_b2", credits=100)
    svc.consumption.consume(
        {"organizationId": org_a, "serviceType": "background_removal"},
        actor_id="owner_a2",
    )
    try:
        svc.consumption.usage_summary(actor_id="owner_b2", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        svc.consumption.consume(
            {"organizationId": org_b, "serviceType": "image_editing"},
            actor_id="editor_1",
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


def test_performance_consume_batch():
    svc = _cm().get_credit_metering_service()
    org_id = _seed_org("owner_p", credits=5000)
    q = svc.quotas.ensure(org_id, plan_key="enterprise")
    assert q.unlimited is True
    start = time.perf_counter()
    for _ in range(40):
        svc.consumption.consume(
            {"organizationId": org_id, "serviceType": "image_editing", "provider": "fal"},
            actor_id="owner_p",
        )
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 5000
    usage = svc.consumption.usage_summary(actor_id="owner_p", organization_id=org_id)
    assert usage["creditsUsed"]["daily"] == 40 * 4
    status = svc.status()
    assert status["stats"]["apiCount"] >= 40

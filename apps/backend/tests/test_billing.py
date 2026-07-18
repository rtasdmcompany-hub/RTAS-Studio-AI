"""Phase 8 Sprint 1 — Billing & Subscription Foundation tests."""

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
    bil.get_billing_service = sys.modules[
        "app.services.billing.service"
    ].get_billing_service
    bil.reset_engine = sys.modules["app.services.billing.service"].reset_engine
    bil.get_engine = sys.modules["app.services.billing.service"].get_engine


_bootstrap()

version = sys.modules["app.services.billing.version"]
catalog = sys.modules["app.services.billing.catalog"]
service_mod = sys.modules["app.services.billing.service"]
errors = sys.modules["app.services.enterprise_auth.errors"]
mt_service = sys.modules["app.services.multi_tenant.service"]


def setup_function():
    service_mod.reset_engine()


def _seed_org(owner: str = "owner_1"):
    mt = mt_service.get_multi_tenant_service()
    slug = f"bill-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Billing Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    ws_id = created["defaultWorkspace"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    mt.add_member({"organizationId": org_id, "userId": "viewer_1", "role": "viewer"})
    return org_id, ws_id


# --- Unit ---


def test_version_unit():
    assert version.PHASE == 8
    assert version.SPRINT == 1
    assert "Billing" in version.ENGINE_NAME


def test_catalog_unit():
    assert "free_trial" in catalog.PLAN_KEYS
    assert "enterprise" in catalog.PLAN_KEYS
    assert catalog.normalize_plan_key("pro") == "professional"
    assert catalog.normalize_cycle("annual") == "yearly"
    assert len(catalog.DEFAULT_PLANS) == 5
    for plan in catalog.DEFAULT_PLANS:
        assert "creditsMonthly" in plan
        assert "maxWorkspaces" in plan
        assert "maxTeams" in plan
        assert "aiProviderLimit" in plan
        assert plan["monthlyPriceUsd"] is not None
        assert plan["yearlyPriceUsd"] is not None


def test_status_unit():
    svc = service_mod.get_billing_service()
    status = svc.status()
    assert status["ok"] is True
    assert status["phase"] == 8
    assert status["sprint"] == 1
    assert status["engines"]["billing"] == "ready"
    assert status["engines"]["subscription"] == "ready"
    assert status["engines"]["plans"] == "ready"
    assert status["engines"]["credits"] == "ready"
    assert status["engines"]["usage"] == "ready"
    assert status["engines"]["invoices"] == "ready"


# --- Plans ---


def test_list_plans():
    svc = service_mod.get_billing_service()
    plans = svc.plans.list_plans()
    assert plans["ok"] is True
    assert plans["count"] == 5
    keys = {p["key"] for p in plans["plans"]}
    assert keys == {
        "free_trial",
        "starter",
        "professional",
        "business",
        "enterprise",
    }
    assert "monthly" in plans["billingCycles"]
    assert "yearly" in plans["billingCycles"]


# --- Subscriptions ---


def test_create_and_get_subscription():
    svc = service_mod.get_billing_service()
    org_id, _ = _seed_org()
    created = svc.subscriptions.create(
        {
            "organizationId": org_id,
            "planKey": "starter",
            "billingCycle": "monthly",
            "companyName": "RTAS Demo",
            "billingEmail": "billing@example.com",
        },
        actor_id="owner_1",
    )
    assert created["ok"] is True
    assert created["subscription"]["planKey"] == "starter"
    assert created["subscription"]["billingCycle"] == "monthly"
    assert created["subscription"]["status"] == "active"
    assert created["credits"]["balance"] == 1000
    assert created["invoice"]["status"] == "open"
    assert created["userSubscription"]["userId"] == "owner_1"

    got = svc.subscriptions.get(actor_id="owner_1", organization_id=org_id)
    assert got["hasSubscription"] is True
    assert got["plan"]["key"] == "starter"


def test_free_trial_subscription():
    svc = service_mod.get_billing_service()
    org_id, _ = _seed_org("owner_trial")
    created = svc.subscriptions.create(
        {"organizationId": org_id, "planKey": "free_trial", "billingCycle": "monthly"},
        actor_id="owner_trial",
    )
    assert created["subscription"]["status"] == "trialing"
    assert created["credits"]["balance"] == 100
    assert created["invoice"]["status"] == "paid"


def test_yearly_enterprise_subscription():
    svc = service_mod.get_billing_service()
    org_id, _ = _seed_org("owner_ent")
    created = svc.subscriptions.create(
        {
            "organizationId": org_id,
            "planKey": "enterprise",
            "billingCycle": "yearly",
        },
        actor_id="owner_ent",
    )
    assert created["subscription"]["billingCycle"] == "yearly"
    assert created["credits"]["balance"] == 1200000
    assert created["plan"]["maxWorkspaces"] == 500
    assert created["plan"]["aiProviderLimit"] == 20


def test_patch_subscription_plan_change():
    svc = service_mod.get_billing_service()
    org_id, _ = _seed_org("owner_up")
    svc.subscriptions.create(
        {"organizationId": org_id, "planKey": "starter", "billingCycle": "monthly"},
        actor_id="owner_up",
    )
    updated = svc.subscriptions.update(
        {
            "organizationId": org_id,
            "planKey": "professional",
            "billingCycle": "yearly",
        },
        actor_id="owner_up",
    )
    assert updated["subscription"]["planKey"] == "professional"
    assert updated["subscription"]["billingCycle"] == "yearly"
    assert updated["invoice"] is not None
    credits = svc.credits.get(org_id, actor_id="owner_up")
    # starter 1000 + professional yearly 60000
    assert credits["wallet"]["balance"] >= 61000


# --- Credits / Usage ---


def test_credits_and_usage():
    svc = service_mod.get_billing_service()
    org_id, ws_id = _seed_org("owner_cred")
    svc.subscriptions.create(
        {"organizationId": org_id, "planKey": "starter"},
        actor_id="owner_cred",
    )
    before = svc.credits.get(org_id, actor_id="owner_cred")
    bal = before["wallet"]["balance"]
    usage = svc.usage.record(
        {
            "organizationId": org_id,
            "workspaceId": ws_id,
            "usageType": "ai_generation",
            "creditsConsumed": 25,
            "provider": "fal",
        },
        actor_id="owner_cred",
    )
    assert usage["ok"] is True
    after = svc.credits.get(org_id, actor_id="owner_cred")
    assert after["wallet"]["balance"] == bal - 25
    listed = svc.usage.list(actor_id="owner_cred", organization_id=org_id)
    assert listed["count"] >= 1
    assert listed["totalCreditsConsumed"] >= 25


# --- Security ---


def test_isolation_and_ownership_security():
    svc = service_mod.get_billing_service()
    org_a, _ = _seed_org("owner_a")
    org_b, _ = _seed_org("owner_b")
    svc.subscriptions.create(
        {"organizationId": org_a, "planKey": "starter"},
        actor_id="owner_a",
    )
    # viewer cannot manage subscription
    try:
        svc.subscriptions.create(
            {"organizationId": org_b, "planKey": "starter"},
            actor_id="viewer_1",
        )
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    # editor cannot manage (needs manager+)
    try:
        svc.subscriptions.update(
            {"organizationId": org_a, "planKey": "business"},
            actor_id="editor_1",
        )
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    # cross-org isolation
    try:
        svc.subscriptions.get(actor_id="owner_b", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    # owner can read own credits
    credits = svc.credits.get(org_a, actor_id="owner_a")
    assert credits["ok"] is True


def test_duplicate_subscription_rejected():
    svc = service_mod.get_billing_service()
    org_id, _ = _seed_org("owner_dup")
    svc.subscriptions.create(
        {"organizationId": org_id, "planKey": "starter"},
        actor_id="owner_dup",
    )
    try:
        svc.subscriptions.create(
            {"organizationId": org_id, "planKey": "business"},
            actor_id="owner_dup",
        )
        assert False, "expected ValidationError"
    except Exception as exc:
        assert "already" in str(exc).lower()

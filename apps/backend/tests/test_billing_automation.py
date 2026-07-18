"""Phase 8 Sprint 5 — Invoicing, Tax, Coupons & Billing Automation tests."""

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
    bil.get_billing_service = sys.modules["app.services.billing.service"].get_billing_service
    bil.reset_engine = sys.modules["app.services.billing.service"].reset_engine

    _load_folder(
        "billing_automation",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    ba = sys.modules["app.services.billing_automation"]
    ba.get_billing_automation_service = sys.modules[
        "app.services.billing_automation.service"
    ].get_billing_automation_service
    ba.reset_engine = sys.modules["app.services.billing_automation.service"].reset_engine


_bootstrap()


def _ba():
    return sys.modules["app.services.billing_automation.service"]


def _mt():
    return sys.modules["app.services.multi_tenant.service"]


def _version():
    return sys.modules["app.services.billing_automation.version"]


def _catalog():
    return sys.modules["app.services.billing_automation.catalog"]


def _errors():
    return sys.modules["app.services.enterprise_auth.errors"]


def _validation():
    return sys.modules["app.services.multi_tenant.validation"]


def setup_function():
    _bootstrap()
    sys.modules["app.services.billing.service"].reset_engine()
    mod = _ba()
    mod._service = None
    sys.modules["app.services.billing_automation.store"].reset_store()


def _seed_org(owner: str = "owner_1"):
    mt = _mt().get_multi_tenant_service()
    slug = f"ba-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Billing Auto Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    return org_id


# --- Unit ---


def test_version_unit():
    version = _version()
    assert version.PHASE == 8
    assert version.SPRINT == 5
    assert "Invoice" in version.ENGINE_NAME or "Invoicing" in version.ENGINE_NAME


def test_catalog_unit():
    catalog = _catalog()
    assert "paid" in catalog.INVOICE_STATUSES
    assert catalog.tax_rule_for("GB")["taxType"] == "vat"
    assert catalog.tax_rule_for("IN")["taxType"] == "gst"
    assert len(catalog.DEFAULT_COUPONS) >= 3
    assert catalog.MAX_PAYMENT_RETRIES == 3


def test_status_unit():
    svc = _ba().get_billing_automation_service()
    status = svc.status()
    assert status["ok"] is True
    assert status["sprint"] == 5
    assert status["engines"]["invoice"] == "ready"
    assert status["engines"]["tax"] == "ready"
    assert status["engines"]["coupon"] == "ready"
    assert status["engines"]["paymentRetry"] == "ready"


# --- Tax ---


def test_tax_vat_gst_and_exemption():
    svc = _ba().get_billing_automation_service()
    org_id = _seed_org("owner_tax")
    uk = svc.tax.get(
        actor_id="owner_tax",
        organization_id=org_id,
        country="GB",
        amount_usd=100.0,
    )
    assert uk["rule"]["taxType"] == "vat"
    assert uk["preview"]["taxUsd"] == 20.0

    au = svc.tax.calculate(
        organization_id=org_id, taxable_usd=100.0, country="AU"
    )
    assert au["tax"]["taxType"] == "gst"
    assert au["tax"]["taxUsd"] == 10.0

    svc.tax.set_exemption(org_id, "nonprofit_resale", actor_id="owner_tax")
    exempt = svc.tax.calculate(
        organization_id=org_id, taxable_usd=100.0, country="US"
    )
    assert exempt["tax"]["exempt"] is True
    assert exempt["tax"]["taxUsd"] == 0.0


# --- Coupons ---


def test_coupon_validate_and_apply():
    svc = _ba().get_billing_automation_service()
    org_id = _seed_org("owner_cpn")
    validated = svc.coupons.validate(
        {"organizationId": org_id, "code": "WELCOME10", "subtotalUsd": 100},
        actor_id="owner_cpn",
    )
    assert validated["valid"] is True
    assert validated["estimatedDiscountUsd"] == 10.0

    applied = svc.coupons.apply(
        {"organizationId": org_id, "code": "SAVE25", "subtotalUsd": 100},
        actor_id="owner_cpn",
    )
    assert applied["discount"]["amountUsd"] == 25.0
    assert applied["usage"]["couponCode"] == "SAVE25"

    try:
        svc.coupons.apply(
            {"organizationId": org_id, "code": "SAVE25", "subtotalUsd": 100},
            actor_id="owner_cpn",
        )
        assert False, "expected per-org limit ValidationError"
    except _validation().ValidationError:
        pass


def test_trial_and_referral_coupons():
    svc = _ba().get_billing_automation_service()
    org_id = _seed_org("owner_ref")
    trial = svc.coupons.validate(
        {"organizationId": org_id, "code": "TRIAL14"},
        actor_id="owner_ref",
    )
    assert trial["trialDays"] == 14
    referral = svc.coupons.apply(
        {"organizationId": org_id, "code": "REFER50", "subtotalUsd": 200},
        actor_id="owner_ref",
    )
    assert referral["discount"]["amountUsd"] == 100.0


# --- Invoices ---


def test_invoice_generation_history_and_status():
    svc = _ba().get_billing_automation_service()
    org_id = _seed_org("owner_inv")
    generated = svc.invoices.generate(
        {
            "organizationId": org_id,
            "planKey": "professional",
            "billingCycle": "monthly",
            "country": "DE",
            "couponCode": "WELCOME10",
        },
        actor_id="owner_inv",
    )
    inv = generated["invoice"]
    assert inv["status"] == "pending"
    assert inv["invoiceNumber"].startswith("INV-")
    assert inv["discountUsd"] == 9.9  # 10% of 99
    assert inv["taxType"] == "vat"
    assert inv["pdfMetadata"]["template"] == "rtas_enterprise_v1"
    assert len(generated["items"]) == 1

    listed = svc.invoices.list(actor_id="owner_inv", organization_id=org_id)
    assert listed["count"] == 1
    got = svc.invoices.get(actor_id="owner_inv", invoice_id=inv["id"])
    assert got["invoice"]["id"] == inv["id"]

    paid = svc.invoices.mark_status(inv["id"], "paid", actor_id="owner_inv")
    assert paid["invoice"]["status"] == "paid"
    assert paid["invoice"]["receiptNumber"]

    refunded = svc.invoices.mark_status(inv["id"], "refunded", actor_id="owner_inv")
    assert refunded["invoice"]["status"] == "refunded"


# --- Automation & Retry ---


def test_billing_automation_renew_remind_expire():
    svc = _ba().get_billing_automation_service()
    org_id = _seed_org("owner_auto")
    # Seed billing subscription for expire path
    billing = sys.modules["app.services.billing.service"].get_billing_service()
    billing.subscriptions.create(
        {"organizationId": org_id, "planKey": "starter", "billingCycle": "monthly"},
        actor_id="owner_auto",
    )
    renewed = svc.automation.renew(
        {
            "organizationId": org_id,
            "planKey": "starter",
            "country": "US",
            "autoPay": True,
        },
        actor_id="owner_auto",
    )
    assert renewed["renewal"] is True
    assert renewed["invoice"]["status"] == "paid"
    assert renewed["receiptNumber"]

    reminder = svc.automation.remind(
        {"organizationId": org_id, "daysBefore": 3},
        actor_id="owner_auto",
    )
    assert reminder["reminder"]["eventType"] == "subscription.reminder"

    expired = svc.automation.expire_subscription(
        {"organizationId": org_id}, actor_id="owner_auto"
    )
    assert expired["expired"] is True


def test_payment_retry_logic():
    svc = _ba().get_billing_automation_service()
    org_id = _seed_org("owner_retry")
    generated = svc.invoices.generate(
        {
            "organizationId": org_id,
            "planKey": "starter",
            "country": "US",
            "status": "pending",
        },
        actor_id="owner_retry",
    )
    invoice_id = generated["invoice"]["id"]

    failed = svc.retries.process(
        {"invoiceId": invoice_id, "forceFail": True},
        actor_id="owner_retry",
    )
    assert failed["succeeded"] is False
    assert failed["invoice"]["status"] == "failed"
    assert failed["retry"]["attempt"] == 1

    failed2 = svc.retries.process(
        {"invoiceId": invoice_id, "forceFail": True},
        actor_id="owner_retry",
    )
    assert failed2["retry"]["attempt"] == 2

    success = svc.retries.process(
        {"invoiceId": invoice_id, "succeed": True},
        actor_id="owner_retry",
    )
    assert success["invoice"]["status"] == "paid"
    assert success["retry"]["status"] == "succeeded"
    assert success["receiptNumber"]


def test_ownership_isolation():
    svc = _ba().get_billing_automation_service()
    org_a = _seed_org("owner_a")
    org_b = _seed_org("owner_b")
    generated = svc.invoices.generate(
        {"organizationId": org_a, "planKey": "starter", "country": "US"},
        actor_id="owner_a",
    )
    try:
        svc.invoices.list(actor_id="owner_b", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        svc.invoices.get(actor_id="owner_b", invoice_id=generated["invoice"]["id"])
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        svc.coupons.apply(
            {"organizationId": org_b, "code": "WELCOME10", "subtotalUsd": 50},
            actor_id="editor_1",
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass

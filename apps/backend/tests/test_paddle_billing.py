"""Phase 8 Sprint 2 — Paddle Billing Integration tests."""

from __future__ import annotations

import hashlib
import hmac
import importlib.util
import json
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
        "paddle_billing",
        ("version", "catalog", "models", "store", "signatures", "service", "engine"),
    )
    pb = sys.modules["app.services.paddle_billing"]
    pb.get_paddle_billing_service = sys.modules[
        "app.services.paddle_billing.service"
    ].get_paddle_billing_service
    pb.reset_engine = sys.modules["app.services.paddle_billing.service"].reset_engine


_bootstrap()

version = sys.modules["app.services.paddle_billing.version"]
catalog = sys.modules["app.services.paddle_billing.catalog"]
signatures = sys.modules["app.services.paddle_billing.signatures"]
service_mod = sys.modules["app.services.paddle_billing.service"]
errors = sys.modules["app.services.enterprise_auth.errors"]
mt_service = sys.modules["app.services.multi_tenant.service"]

SECRET = "test_paddle_webhook_secret_123"


def setup_function():
    service_mod.reset_engine()


def _seed_org(owner: str = "owner_1"):
    mt = mt_service.get_multi_tenant_service()
    slug = f"pad-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Paddle Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    return org_id


def _sign(body: bytes, secret: str = SECRET) -> str:
    ts = str(int(time.time()))
    digest = hmac.new(
        secret.encode("utf-8"), ts.encode("utf-8") + b":" + body, hashlib.sha256
    ).hexdigest()
    return f"ts={ts};h1={digest}"


# --- Unit ---


def test_version_unit():
    assert version.PHASE == 8
    assert version.SPRINT == 2
    assert "Paddle" in version.ENGINE_NAME


def test_catalog_unit():
    assert "subscription.created" in catalog.WEBHOOK_EVENTS
    assert "payment.failed" in catalog.WEBHOOK_EVENTS
    assert catalog.resolve_price_id("starter", "monthly")
    products = catalog.product_catalog()
    assert len(products) == 5


def test_signature_unit():
    body = b'{"event_type":"subscription.created"}'
    header = _sign(body)
    ok = signatures.verify_paddle_signature(header, body, secret=SECRET)
    assert ok["ok"] is True
    try:
        signatures.verify_paddle_signature("ts=1;h1=bad", body, secret=SECRET)
        assert False, "expected SignatureError"
    except signatures.SignatureError:
        pass


def test_status_unit():
    svc = service_mod.get_paddle_billing_service()
    status = svc.status()
    assert status["ok"] is True
    assert status["sprint"] == 2
    assert status["engines"]["webhooks"] == "ready"
    assert status["engines"]["checkout"] == "ready"


# --- Checkout / Customer ---


def test_checkout_and_customer():
    svc = service_mod.get_paddle_billing_service()
    org_id = _seed_org()
    checkout = svc.checkout.create(
        {
            "organizationId": org_id,
            "planKey": "professional",
            "billingCycle": "yearly",
            "email": "bill@rtas.test",
            "countryCode": "PK",
            "taxIdentifier": "TAX-1",
            "address": {"line1": "1 Studio Way", "city": "Karachi"},
        },
        actor_id="owner_1",
    )
    assert checkout["ok"] is True
    assert checkout["checkout"]["planKey"] == "professional"
    assert checkout["checkout"]["billingCycle"] == "yearly"
    assert "price_id=" in checkout["checkout"]["checkoutUrl"]
    assert checkout["customer"]["countryCode"] == "PK"
    assert checkout["customer"]["taxIdentifier"] == "TAX-1"

    customer = svc.customers.get(actor_id="owner_1", organization_id=org_id)
    assert customer["customer"]["email"] == "bill@rtas.test"


# --- Webhooks ---


def test_webhook_subscription_lifecycle():
    import os

    os.environ["PADDLE_WEBHOOK_SECRET"] = SECRET
    svc = service_mod.get_paddle_billing_service()
    org_id = _seed_org("owner_wh")
    # seed customer via checkout
    svc.checkout.create(
        {
            "organizationId": org_id,
            "planKey": "starter",
            "billingCycle": "monthly",
            "email": "wh@rtas.test",
        },
        actor_id="owner_wh",
    )
    cust = svc.customers.get(actor_id="owner_wh", organization_id=org_id)["customer"]

    payload = {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "event_type": "subscription.created",
        "data": {
            "id": f"sub_{uuid.uuid4().hex[:12]}",
            "status": "active",
            "customer_id": cust["paddleCustomerId"],
            "custom_data": {
                "organization_id": org_id,
                "plan_key": "starter",
                "billing_cycle": "monthly",
            },
            "items": [{"price": {"id": "pri_starter_monthly"}}],
        },
    }
    body = json.dumps(payload).encode("utf-8")
    result = svc.webhooks.process(
        raw_body=body,
        signature_header=_sign(body),
        allow_unsigned=False,
    )
    assert result["ok"] is True
    assert result["handled"] is True
    assert result["subscription"]["status"] == "active"

    status = svc.subscriptions.status(actor_id="owner_wh", organization_id=org_id)
    assert status["hasActiveSubscription"] is True

    # payment failed → past_due
    fail = {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "event_type": "payment.failed",
        "data": {
            "customer_id": cust["paddleCustomerId"],
            "custom_data": {"organization_id": org_id},
        },
    }
    fbody = json.dumps(fail).encode("utf-8")
    failed = svc.webhooks.process(
        raw_body=fbody, signature_header=_sign(fbody), allow_unsigned=False
    )
    assert failed["status"] == "past_due"

    # resume via API
    resumed = svc.subscriptions.resume(
        {"organizationId": org_id}, actor_id="owner_wh"
    )
    assert resumed["subscription"]["status"] == "active"

    # cancel
    canceled = svc.subscriptions.cancel(
        {"organizationId": org_id, "immediate": True}, actor_id="owner_wh"
    )
    assert canceled["subscription"]["status"] == "canceled"

    # resume again
    resumed2 = svc.subscriptions.resume(
        {"organizationId": org_id}, actor_id="owner_wh"
    )
    assert resumed2["subscription"]["status"] == "active"


def test_webhook_rejects_bad_signature():
    import os

    os.environ["PADDLE_WEBHOOK_SECRET"] = SECRET
    svc = service_mod.get_paddle_billing_service()
    body = b'{"event_type":"subscription.created","event_id":"x","data":{}}'
    try:
        svc.webhooks.process(
            raw_body=body,
            signature_header="ts=1;h1=deadbeef",
            allow_unsigned=False,
        )
        assert False, "expected SignatureError"
    except signatures.SignatureError:
        pass


def test_webhook_transaction_and_refund():
    import os

    os.environ["PADDLE_WEBHOOK_SECRET"] = SECRET
    svc = service_mod.get_paddle_billing_service()
    org_id = _seed_org("owner_txn")
    svc.checkout.create(
        {
            "organizationId": org_id,
            "planKey": "business",
            "email": "txn@rtas.test",
        },
        actor_id="owner_txn",
    )
    cust = svc.customers.get(actor_id="owner_txn", organization_id=org_id)["customer"]
    # create subscription first
    sub_payload = {
        "event_id": f"evt_{uuid.uuid4().hex[:10]}",
        "event_type": "subscription.created",
        "data": {
            "id": "sub_txn_1",
            "status": "active",
            "customer_id": cust["paddleCustomerId"],
            "custom_data": {
                "organization_id": org_id,
                "plan_key": "business",
                "billing_cycle": "monthly",
            },
        },
    }
    sbody = json.dumps(sub_payload).encode("utf-8")
    svc.webhooks.process(raw_body=sbody, signature_header=_sign(sbody))

    txn_payload = {
        "event_id": f"evt_{uuid.uuid4().hex[:10]}",
        "event_type": "transaction.completed",
        "data": {
            "id": "txn_1",
            "subscription_id": "sub_txn_1",
            "customer_id": cust["paddleCustomerId"],
            "custom_data": {"organization_id": org_id},
            "details": {"totals": {"grand_total": 29900}},
        },
    }
    tbody = json.dumps(txn_payload).encode("utf-8")
    txn = svc.webhooks.process(raw_body=tbody, signature_header=_sign(tbody))
    assert txn["handled"] is True
    assert txn["transaction"]["status"] == "completed"

    refund_payload = {
        "event_id": f"evt_{uuid.uuid4().hex[:10]}",
        "event_type": "refund.completed",
        "data": {
            "id": "ref_1",
            "customer_id": cust["paddleCustomerId"],
            "custom_data": {"organization_id": org_id},
        },
    }
    rbody = json.dumps(refund_payload).encode("utf-8")
    refund = svc.webhooks.process(raw_body=rbody, signature_header=_sign(rbody))
    assert refund["handled"] is True


# --- Security ---


def test_ownership_isolation():
    svc = service_mod.get_paddle_billing_service()
    org_a = _seed_org("owner_a")
    org_b = _seed_org("owner_b")
    svc.checkout.create(
        {"organizationId": org_a, "planKey": "starter", "email": "a@t.com"},
        actor_id="owner_a",
    )
    try:
        svc.customers.get(actor_id="owner_b", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    try:
        svc.checkout.create(
            {"organizationId": org_b, "planKey": "starter", "email": "x@t.com"},
            actor_id="editor_1",
        )
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass

"""Phase 8 Sprint 3 — PayPal, Credit Wallet & Payment Processing tests."""

from __future__ import annotations

import importlib.util
import json
import os
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
        "payment_processing",
        (
            "version",
            "catalog",
            "models",
            "store",
            "signatures",
            "service",
            "engine",
        ),
    )
    pp = sys.modules["app.services.payment_processing"]
    pp.get_payment_processing_service = sys.modules[
        "app.services.payment_processing.service"
    ].get_payment_processing_service
    pp.reset_engine = sys.modules["app.services.payment_processing.service"].reset_engine


_bootstrap()

version = sys.modules["app.services.payment_processing.version"]
catalog = sys.modules["app.services.payment_processing.catalog"]
signatures = sys.modules["app.services.payment_processing.signatures"]
service_mod = sys.modules["app.services.payment_processing.service"]
errors = sys.modules["app.services.enterprise_auth.errors"]
mt_service = sys.modules["app.services.multi_tenant.service"]

SECRET = "test_paypal_webhook_secret_abc"


def setup_function():
    service_mod.reset_engine()
    for key in (
        "PAYPAL_CLIENT_ID",
        "PAYPAL_WEBHOOK_ID",
        "PAYPAL_WEBHOOK_SECRET",
    ):
        os.environ.pop(key, None)


def _seed_org(owner: str = "owner_1"):
    mt = mt_service.get_multi_tenant_service()
    slug = f"pp-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "PayPal Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    return org_id


def _sign(body: bytes, *, tid: str = "tx-1", ts: str = "2026-07-19T00:00:00Z") -> str:
    return signatures.compute_transmission_hash(
        transmission_id=tid,
        timestamp=ts,
        webhook_id=SECRET,
        raw_body=body,
    )


# --- Unit ---


def test_version_unit():
    assert version.PHASE == 8
    assert version.SPRINT == 3
    assert "PayPal" in version.ENGINE_NAME


def test_catalog_unit():
    assert "PAYMENT.CAPTURE.COMPLETED" in catalog.PAYPAL_WEBHOOK_EVENTS
    assert "purchase" in catalog.CREDIT_TXN_TYPES
    pack = catalog.get_pack("pack_500")
    assert pack["credits"] == 500
    assert catalog.total_credits(pack) == 550


def test_signature_unit():
    body = b'{"event_type":"PAYMENT.CAPTURE.COMPLETED"}'
    sig = _sign(body)
    ok = signatures.verify_paypal_webhook(
        transmission_id="tx-1",
        transmission_time="2026-07-19T00:00:00Z",
        transmission_sig=sig,
        raw_body=body,
        webhook_id=SECRET,
    )
    assert ok["ok"] is True
    try:
        signatures.verify_paypal_webhook(
            transmission_id="tx-1",
            transmission_time="2026-07-19T00:00:00Z",
            transmission_sig="deadbeef",
            raw_body=body,
            webhook_id=SECRET,
        )
        assert False, "expected SignatureError"
    except signatures.SignatureError:
        pass


def test_status_unit():
    svc = service_mod.get_payment_processing_service()
    status = svc.status()
    assert status["ok"] is True
    assert status["sprint"] == 3
    assert status["engines"]["paypal"] == "ready"
    assert status["engines"]["wallet"] == "ready"
    assert status["engines"]["refunds"] == "ready"


# --- PayPal / Wallet ---


def test_paypal_create_and_capture():
    svc = service_mod.get_payment_processing_service()
    org_id = _seed_org()
    order = svc.paypal.create_order(
        {"organizationId": org_id, "packKey": "pack_500"},
        actor_id="owner_1",
    )
    assert order["ok"] is True
    assert order["order"]["status"] == "CREATED"
    assert order["order"]["credits"] == 550

    captured = svc.paypal.capture_order(
        {
            "orderId": order["order"]["id"],
            "capture": {"status": "COMPLETED", "simulated": True},
            "payerEmail": "buyer@rtas.test",
        },
        actor_id="owner_1",
    )
    assert captured["ok"] is True
    assert captured["payment"]["status"] == "COMPLETED"
    assert captured["payment"]["verified"] is True
    assert captured["wallet"]["balance"] == 550

    wallet = svc.wallets.get(actor_id="owner_1", organization_id=org_id)
    assert wallet["wallet"]["balance"] == 550
    assert wallet["wallet"]["bonusBalance"] == 50


def test_wallet_purchase_history_and_consume():
    svc = service_mod.get_payment_processing_service()
    org_id = _seed_org("owner_buy")
    purchased = svc.purchases.purchase(
        {
            "organizationId": org_id,
            "packKey": "pack_100",
            "awardTrial": True,
            "trialCredits": 40,
            "awardPromo": True,
            "promoCredits": 10,
        },
        actor_id="owner_buy",
    )
    assert purchased["ok"] is True
    # 100 purchased + 40 trial + 10 promo
    assert purchased["wallet"]["balance"] == 150
    assert purchased["wallet"]["trialBalance"] == 40
    assert purchased["wallet"]["promoBalance"] == 10

    history = svc.transactions.history(actor_id="owner_buy", organization_id=org_id)
    types = {t["type"] for t in history["transactions"]}
    assert "purchase" in types
    assert "trial" in types
    assert "promotional" in types

    consumed = svc.transactions.debit(
        org_id, 30, actor_id="owner_buy", reason="generate_video"
    )
    assert consumed["wallet"]["balance"] == 120
    assert consumed["wallet"]["lifetimeConsumed"] == 30

    pay_hist = svc.history.list(actor_id="owner_buy", organization_id=org_id)
    assert pay_hist["count"] >= 2


def test_wallet_refund_payment_claws_back():
    svc = service_mod.get_payment_processing_service()
    org_id = _seed_org("owner_ref")
    bought = svc.purchases.purchase(
        {"organizationId": org_id, "packKey": "pack_100"},
        actor_id="owner_ref",
    )
    payment_id = bought["payment"]["id"]
    assert bought["wallet"]["balance"] == 100

    refunded = svc.refunds.request(
        {
            "organizationId": org_id,
            "paymentId": payment_id,
            "autoProcess": True,
        },
        actor_id="owner_ref",
    )
    assert refunded["ok"] is True
    assert refunded["refund"]["status"] == "completed"
    assert refunded["wallet"]["balance"] == 0
    assert refunded["refund"]["credits"] == 100
    wallet = svc.wallets.get(actor_id="owner_ref", organization_id=org_id)
    assert wallet["wallet"]["lifetimeRefunded"] == 100


def test_standalone_credit_refund_restores():
    svc = service_mod.get_payment_processing_service()
    org_id = _seed_org("owner_cr")
    svc.transactions.credit(
        org_id,
        20,
        txn_type="adjustment",
        credit_category="purchased",
        actor_id="owner_cr",
        reason="seed",
    )
    svc.transactions.debit(org_id, 20, actor_id="owner_cr", reason="used")
    assert svc.wallets.get(actor_id="owner_cr", organization_id=org_id)["wallet"]["balance"] == 0

    restored = svc.refunds.request(
        {
            "organizationId": org_id,
            "credits": 20,
            "reason": "failed_job",
            "autoProcess": True,
        },
        actor_id="owner_cr",
    )
    assert restored["refund"]["status"] == "completed"
    assert restored["wallet"]["balance"] == 20


def test_paypal_webhook_capture_and_denied():
    os.environ["PAYPAL_WEBHOOK_ID"] = SECRET
    svc = service_mod.get_payment_processing_service()
    org_id = _seed_org("owner_wh")
    order = svc.paypal.create_order(
        {"organizationId": org_id, "packKey": "pack_500"},
        actor_id="owner_wh",
    )
    order_id = order["order"]["id"]
    payload = {
        "id": f"WH-{uuid.uuid4().hex[:10]}",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {"id": "CAP-WH-1", "supplementary_data": {"related_ids": {"order_id": order_id}}},
    }
    body = json.dumps(payload).encode("utf-8")
    tid, ts = "tx-wh-1", "2026-07-19T01:00:00Z"
    result = svc.paypal.webhook(
        raw_body=body,
        transmission_id=tid,
        transmission_time=ts,
        transmission_sig=_sign(body, tid=tid, ts=ts),
        allow_unsigned=False,
    )
    assert result["ok"] is True
    assert result["payment"]["status"] == "COMPLETED"
    wallet = svc.wallets.get(actor_id="owner_wh", organization_id=org_id)
    assert wallet["wallet"]["balance"] == 550

    # Denied path on a fresh order
    order2 = svc.paypal.create_order(
        {"organizationId": org_id, "packKey": "pack_100"},
        actor_id="owner_wh",
    )
    deny = {
        "id": f"WH-{uuid.uuid4().hex[:10]}",
        "event_type": "PAYMENT.CAPTURE.DENIED",
        "resource": {"id": order2["order"]["id"]},
    }
    dbody = json.dumps(deny).encode("utf-8")
    tid2, ts2 = "tx-wh-2", "2026-07-19T01:05:00Z"
    denied = svc.paypal.webhook(
        raw_body=dbody,
        transmission_id=tid2,
        transmission_time=ts2,
        transmission_sig=_sign(dbody, tid=tid2, ts=ts2),
        allow_unsigned=False,
    )
    assert denied["status"] == "FAILED"


def test_webhook_rejects_bad_signature():
    os.environ["PAYPAL_WEBHOOK_ID"] = SECRET
    svc = service_mod.get_payment_processing_service()
    body = b'{"event_type":"PAYMENT.CAPTURE.COMPLETED","id":"x","resource":{}}'
    try:
        svc.paypal.webhook(
            raw_body=body,
            transmission_id="tx",
            transmission_time="t",
            transmission_sig="bad",
            allow_unsigned=False,
        )
        assert False, "expected SignatureError"
    except signatures.SignatureError:
        pass


# --- Security ---


def test_ownership_isolation():
    svc = service_mod.get_payment_processing_service()
    org_a = _seed_org("owner_a")
    org_b = _seed_org("owner_b")
    svc.purchases.purchase(
        {"organizationId": org_a, "packKey": "pack_100"},
        actor_id="owner_a",
    )
    try:
        svc.wallets.get(actor_id="owner_b", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    try:
        svc.purchases.purchase(
            {"organizationId": org_b, "packKey": "pack_100"},
            actor_id="editor_1",
        )
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass

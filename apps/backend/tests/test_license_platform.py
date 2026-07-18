"""Phase 8 Sprint 7 — Enterprise License, API Access & Developer Platform tests."""

from __future__ import annotations

import importlib.util
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
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
        "license_platform",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    lp = sys.modules["app.services.license_platform"]
    lp.get_license_platform_service = sys.modules[
        "app.services.license_platform.service"
    ].get_license_platform_service
    lp.reset_engine = sys.modules["app.services.license_platform.service"].reset_engine


_bootstrap()


def _lp():
    return sys.modules["app.services.license_platform.service"]


def _mt():
    return sys.modules["app.services.multi_tenant.service"]


def _version():
    return sys.modules["app.services.license_platform.version"]


def _catalog():
    return sys.modules["app.services.license_platform.catalog"]


def _errors():
    return sys.modules["app.services.enterprise_auth.errors"]


def _validation():
    return sys.modules["app.services.multi_tenant.validation"]


def setup_function():
    _bootstrap()
    mod = _lp()
    mod._service = None
    sys.modules["app.services.license_platform.store"].reset_store()


def _seed_org(owner: str = "owner_1"):
    mt = _mt().get_multi_tenant_service()
    slug = f"lp-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "License Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    return org_id


def _svc():
    return _lp().get_license_platform_service()


# --- Unit ---


def test_version_unit():
    v = _version()
    assert v.PHASE == 8
    assert v.SPRINT == 7
    assert "License" in v.ENGINE_NAME
    assert "Developer Platform" in v.ENGINE_NAME


def test_catalog_unit():
    c = _catalog()
    assert c.LICENSE_TIERS == ("free", "trial", "starter", "professional", "business", "enterprise")
    assert c.rate_policy("enterprise") == {"perMinute": 0, "perHour": 0, "perDay": 0}
    assert c.rate_policy("free")["perMinute"] == 10
    key = c.generate_license_key()
    assert key.startswith("RTAS-") and len(key) == 24
    assert len(c.generate_secret(40)) == 40
    assert c.WEBHOOK_MAX_RETRIES == 5


def test_status_unit():
    status = _svc().status()
    assert status["ok"] is True
    assert status["sprint"] == 7
    for engine in (
        "licenseManagement",
        "licenseValidation",
        "apiKeys",
        "personalAccessTokens",
        "developerPlatform",
        "rateLimiting",
    ):
        assert status["engines"][engine] == "ready"


# --- Licenses ---


def test_license_activation_and_status():
    org_id = _seed_org("owner_la")
    svc = _svc()
    result = svc.licenses.activate(
        {"organizationId": org_id, "tier": "professional", "seats": 5},
        actor_id="owner_la",
    )
    lic = result["license"]
    assert lic["tier"] == "professional"
    assert lic["status"] == "active"
    assert lic["licenseKey"].startswith("RTAS-")
    assert lic["seats"] == 5
    assert lic["expiresAt"] is not None

    status = svc.licenses.status(actor_id="owner_la", organization_id=org_id)
    assert status["license"]["status"] == "active"
    assert "****" in status["license"]["licenseKey"]  # masked
    assert status["rateLimits"]["perMinute"] == 120
    assert any(h["action"] == "activated" for h in status["history"])

    # Cannot double-activate
    try:
        svc.licenses.activate({"organizationId": org_id, "tier": "starter"}, actor_id="owner_la")
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "already has an active license" in str(exc)


def test_license_validation_and_expiry():
    org_id = _seed_org("owner_lv")
    svc = _svc()
    lic = svc.licenses.activate(
        {"organizationId": org_id, "tier": "trial"}, actor_id="owner_lv"
    )["license"]
    valid = svc.validator.validate(lic["licenseKey"])
    assert valid["valid"] is True
    assert valid["tier"] == "trial"

    unknown = svc.validator.validate("RTAS-XXXX-XXXX-XXXX-XXXX")
    assert unknown["valid"] is False

    # Force expiry
    store = sys.modules["app.services.license_platform.store"]
    raw = store.get_license_by_org(org_id)
    raw.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    store.save_license(raw)
    expired = svc.validator.validate(lic["licenseKey"])
    assert expired["valid"] is False
    assert expired["status"] == "expired"

    history = svc.licenses.history(actor_id="owner_lv", organization_id=org_id)
    assert any(h["action"] == "expired" for h in history["history"])


def test_license_renew_suspend_revoke():
    org_id = _seed_org("owner_lr")
    svc = _svc()
    svc.licenses.activate({"organizationId": org_id, "tier": "starter"}, actor_id="owner_lr")

    renewed = svc.licenses.renew(
        {"organizationId": org_id, "tier": "business"}, actor_id="owner_lr"
    )
    assert renewed["license"]["tier"] == "business"
    assert renewed["license"]["status"] == "active"

    suspended = svc.licenses.suspend(org_id, actor_id="owner_lr", reason="payment issue")
    assert suspended["license"]["status"] == "suspended"
    resumed = svc.licenses.resume(org_id, actor_id="owner_lr")
    assert resumed["license"]["status"] == "active"

    revoked = svc.licenses.revoke({"organizationId": org_id}, actor_id="owner_lr")
    assert revoked["license"]["status"] == "revoked"
    try:
        svc.licenses.renew({"organizationId": org_id}, actor_id="owner_lr")
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "revoked" in str(exc)

    actions = [
        h["action"]
        for h in svc.licenses.history(actor_id="owner_lr", organization_id=org_id)["history"]
    ]
    for expected in ("activated", "renewed", "suspended", "resumed", "revoked"):
        assert expected in actions


# --- API keys ---


def test_api_key_create_list_and_secret_storage():
    org_id = _seed_org("owner_ak")
    svc = _svc()
    created = svc.keys.create(
        {"organizationId": org_id, "keyType": "personal", "access": "read_only"},
        actor_id="owner_ak",
    )
    key = created["apiKey"]
    assert key["secret"].startswith("rtas_per_")
    assert all(s.endswith(":read") for s in key["scopes"])

    # Secret is never stored in plaintext — only hash
    store = sys.modules["app.services.license_platform.store"]
    raw = store.get_api_key(key["id"])
    assert raw.key_hash != key["secret"]
    assert len(raw.key_hash) == 64
    assert key["secret"] not in str(raw.to_dict())

    listed = svc.keys.list(actor_id="owner_ak", organization_id=org_id)
    assert listed["count"] == 1
    assert "secret" not in listed["apiKeys"][0]

    # Authentication resolves the secret
    resolved = svc.keys.authenticate(key["secret"])
    assert resolved is not None and resolved.id == key["id"]
    assert svc.keys.authenticate("rtas_per_invalid") is None


def test_api_key_types_scopes_and_workspace():
    org_id = _seed_org("owner_kt")
    svc = _svc()
    org_key = svc.keys.create(
        {"organizationId": org_id, "keyType": "organization", "access": "full_access"},
        actor_id="owner_kt",
    )["apiKey"]
    assert org_key["keyType"] == "organization"
    assert len(org_key["scopes"]) == len(_catalog().API_SCOPES)

    ws_key = svc.keys.create(
        {
            "organizationId": org_id,
            "keyType": "workspace",
            "workspaceId": "ws_123",
            "access": "scoped",
            "scopes": ["generate:read", "assets:read"],
        },
        actor_id="owner_kt",
    )["apiKey"]
    assert ws_key["workspaceId"] == "ws_123"
    assert ws_key["scopes"] == ["generate:read", "assets:read"]

    # Workspace key without workspaceId fails
    try:
        svc.keys.create(
            {"organizationId": org_id, "keyType": "workspace"}, actor_id="owner_kt"
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass

    # Unknown scope fails
    try:
        svc.keys.create(
            {
                "organizationId": org_id,
                "access": "scoped",
                "scopes": ["nuclear:launch"],
            },
            actor_id="owner_kt",
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "unknown scopes" in str(exc)


def test_api_key_rotation_and_revocation():
    org_id = _seed_org("owner_kr")
    svc = _svc()
    created = svc.keys.create({"organizationId": org_id}, actor_id="owner_kr")["apiKey"]
    old_secret = created["secret"]

    rotated = svc.keys.rotate(created["id"], actor_id="owner_kr")["apiKey"]
    new_secret = rotated["secret"]
    assert new_secret != old_secret
    assert svc.keys.authenticate(old_secret) is None
    assert svc.keys.authenticate(new_secret) is not None

    revoked = svc.keys.revoke(created["id"], actor_id="owner_kr")["apiKey"]
    assert revoked["active"] is False
    assert svc.keys.authenticate(new_secret) is None
    try:
        svc.keys.rotate(created["id"], actor_id="owner_kr")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


# --- Personal access tokens ---


def test_personal_access_tokens():
    org_id = _seed_org("owner_pt")
    svc = _svc()
    created = svc.tokens.create(
        {"organizationId": org_id, "name": "ci token", "scopes": ["projects:read"]},
        actor_id="owner_pt",
    )["token"]
    assert created["secret"].startswith("rtas_pat_")
    assert created["expiresAt"] is not None

    assert svc.tokens.authenticate(created["secret"]) is not None

    listed = svc.tokens.list(actor_id="owner_pt")
    assert listed["count"] == 1

    # Another user cannot revoke it
    try:
        svc.tokens.revoke(created["id"], actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    revoked = svc.tokens.revoke(created["id"], actor_id="owner_pt")["token"]
    assert revoked["active"] is False
    assert svc.tokens.authenticate(created["secret"]) is None


# --- Rate limiting ---


def test_rate_limit_free_tier_enforced():
    org_id = _seed_org("owner_rl")
    svc = _svc()
    # Free tier: 10/minute
    allowed = 0
    blocked = 0
    for _ in range(12):
        result = svc.rate_limits.check(org_id)
        if result["allowed"]:
            allowed += 1
        else:
            blocked += 1
    assert allowed == 10
    assert blocked == 2

    status = svc.rate_limits.status(actor_id="owner_rl", organization_id=org_id)
    assert status["tier"] == "free"
    assert status["state"]["usage"]["minute"] == 10


def test_rate_limit_tiers_and_enterprise_unlimited():
    org_id = _seed_org("owner_ru")
    svc = _svc()
    svc.licenses.activate(
        {"organizationId": org_id, "tier": "enterprise"}, actor_id="owner_ru"
    )
    for _ in range(50):
        result = svc.rate_limits.check(org_id)
        assert result["allowed"] is True
    assert result["unlimited"] is True

    # Workspace scope gets a fraction of org limits
    org2 = _seed_org("owner_rw")
    svc.licenses.activate({"organizationId": org2, "tier": "starter"}, actor_id="owner_rw")
    ws = svc.rate_limits.check(org2, scope="workspace", scope_id="ws_9")
    assert ws["state"]["limits"]["perMinute"] == 30  # 50% of starter's 60


# --- Webhooks ---


def test_webhook_registration_and_delivery():
    org_id = _seed_org("owner_wh")
    svc = _svc()
    hook = svc.platform.register_webhook(
        {
            "organizationId": org_id,
            "url": "https://example.com/hooks/rtas",
            "events": ["generation.completed", "invoice.paid"],
        },
        actor_id="owner_wh",
    )["webhook"]
    assert hook["secret"].startswith("rtas_whsec_")
    assert hook["active"] is True

    # https required
    try:
        svc.platform.register_webhook(
            {"organizationId": org_id, "url": "http://insecure.com", "events": ["invoice.paid"]},
            actor_id="owner_wh",
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass

    deliveries = svc.platform.emit(
        org_id, "generation.completed", {"jobId": "job_1"}
    )
    assert len(deliveries) == 1
    assert deliveries[0].status == "delivered"

    # Non-matching event produces no delivery
    assert svc.platform.emit(org_id, "payout.paid") == []

    listed = svc.platform.list_webhooks(actor_id="owner_wh", organization_id=org_id)
    assert listed["count"] == 1


def test_webhook_retry_queue_and_exhaustion():
    org_id = _seed_org("owner_wr")
    svc = _svc()
    svc.platform.register_webhook(
        {"organizationId": org_id, "url": "https://example.com/x", "events": ["invoice.failed"]},
        actor_id="owner_wr",
    )
    delivery = svc.platform.emit(org_id, "invoice.failed", deliver=False)[0]
    assert delivery.status == "pending"

    for i in range(1, 5):
        failed = svc.platform.fail_delivery(delivery.id, f"timeout {i}")
        assert failed.status == "failed"
        assert failed.next_retry_at is not None
    exhausted = svc.platform.fail_delivery(delivery.id, "final failure")
    assert exhausted.status == "exhausted"
    assert exhausted.attempts == 5

    queue = svc.platform.retry_queue(actor_id="owner_wr", organization_id=org_id)
    assert len(queue["exhausted"]) == 1
    assert len(queue["pendingRetries"]) == 0


def test_webhook_management():
    org_id = _seed_org("owner_wm")
    svc = _svc()
    hook = svc.platform.register_webhook(
        {"organizationId": org_id, "url": "https://example.com/y", "events": ["credits.low"]},
        actor_id="owner_wm",
    )["webhook"]
    disabled = svc.platform.set_webhook_active(hook["id"], False, actor_id="owner_wm")
    assert disabled["webhook"]["active"] is False
    assert svc.platform.emit(org_id, "credits.low") == []

    deleted = svc.platform.delete_webhook(hook["id"], actor_id="owner_wm")
    assert deleted["deleted"] is True
    assert svc.platform.list_webhooks(actor_id="owner_wm", organization_id=org_id)["count"] == 0


# --- Developer platform ---


def test_docs_and_usage_stats():
    org_id = _seed_org("owner_du")
    svc = _svc()
    docs = svc.platform.docs()
    assert docs["documentation"]["specFormat"] == "openapi-3.1"
    assert len(docs["sdks"]) == 3
    assert "generation.completed" in docs["webhookEvents"]

    for i in range(10):
        svc.platform.record_usage(
            org_id,
            endpoint="/api/generate",
            method="POST",
            status_code=200 if i < 8 else 500,
            latency_ms=100.0 + i,
        )
    usage = svc.platform.usage(actor_id="owner_du", organization_id=org_id)["usage"]
    assert usage["totalRequests"] == 10
    assert usage["errorCount"] == 2
    assert usage["errorRatePct"] == 20.0
    assert usage["byEndpoint"]["/api/generate"] == 10


# --- Security ---


def test_ownership_isolation():
    org_a = _seed_org("owner_sa")
    org_b = _seed_org("owner_sb")
    svc = _svc()
    svc.licenses.activate({"organizationId": org_a, "tier": "starter"}, actor_id="owner_sa")

    # Non-member cannot read license status / keys / usage
    try:
        svc.licenses.status(actor_id="owner_sb", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        svc.keys.list(actor_id="owner_sb", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        svc.platform.usage(actor_id="owner_sb", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass

    # Member (editor) cannot manage licenses or org keys
    try:
        svc.licenses.revoke({"organizationId": org_b}, actor_id="editor_1")
        assert False, "expected access error"
    except (_errors().ForbiddenError, _errors().NotFoundError):
        pass
    try:
        svc.keys.create(
            {"organizationId": org_b, "keyType": "organization"}, actor_id="editor_1"
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass

    # Personal keys of one user are hidden from another member's list
    mine = svc.keys.create({"organizationId": org_b, "keyType": "personal"}, actor_id="owner_sb")
    svc.keys.create({"organizationId": org_b, "keyType": "personal"}, actor_id="editor_1")
    listed = svc.keys.list(actor_id="editor_1", organization_id=org_b)
    ids = [k["id"] for k in listed["apiKeys"]]
    assert mine["apiKey"]["id"] not in ids


# --- Performance ---


def test_performance_bulk_operations():
    org_id = _seed_org("owner_pf")
    svc = _svc()
    svc.licenses.activate(
        {"organizationId": org_id, "tier": "enterprise"}, actor_id="owner_pf"
    )
    start = time.perf_counter()
    for _ in range(300):
        assert svc.rate_limits.check(org_id)["allowed"] is True
    for i in range(200):
        svc.platform.record_usage(org_id, endpoint=f"/api/e{i % 5}", latency_ms=50.0)
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0

    usage = svc.platform.usage(actor_id="owner_pf", organization_id=org_id)["usage"]
    assert usage["totalRequests"] == 200
    metrics = sys.modules["app.services.license_platform.store"].metrics()
    assert metrics["errorCount"] == 0

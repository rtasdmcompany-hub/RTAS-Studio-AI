"""Phase 9 Sprint 8 — Enterprise Automation, Integrations & Event-Driven Platform tests."""

from __future__ import annotations

import importlib.util
import json
import sys
import time
import uuid
from datetime import timedelta
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
        "enterprise_automation",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    autom = sys.modules["app.services.enterprise_automation"]
    autom.get_enterprise_automation_service = sys.modules[
        "app.services.enterprise_automation.service"
    ].get_enterprise_automation_service
    autom.reset_engine = sys.modules[
        "app.services.enterprise_automation.service"
    ].reset_engine


_bootstrap()


def _ea():
    return sys.modules["app.services.enterprise_automation.service"]


def _mt():
    return sys.modules["app.services.multi_tenant.service"]


def _version():
    return sys.modules["app.services.enterprise_automation.version"]


def _catalog():
    return sys.modules["app.services.enterprise_automation.catalog"]


def _errors():
    return sys.modules["app.services.enterprise_auth.errors"]


def _validation():
    return sys.modules["app.services.multi_tenant.validation"]


def setup_function():
    _bootstrap()
    mod = _ea()
    mod._service = None
    sys.modules["app.services.enterprise_automation.store"].reset_store()


def _seed_org(owner: str = "owner_1"):
    mt = _mt().get_multi_tenant_service()
    slug = f"ea-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Automation Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    return org_id


def _svc():
    return _ea().get_enterprise_automation_service()


def _create_rule(org_id: str, actor: str, **overrides):
    payload = {
        "organizationId": org_id,
        "name": "On AI Complete",
        "mode": "event",
        "triggerEvent": "ai.job.completed",
        "actions": [{"type": "notify"}],
    }
    payload.update(overrides)
    return _svc().automation.create(payload, actor_id=actor)


# --- Unit ---


def test_version_unit():
    v = _version()
    assert v.PHASE == 9
    assert v.SPRINT == 8
    assert "Automation" in v.ENGINE_NAME


def test_catalog_unit():
    c = _catalog()
    assert "event" in c.AUTOMATION_MODES
    assert "queue" in c.AUTOMATION_MODES
    assert "user.registered" in c.EVENT_TYPES
    assert "ai.job.completed" in c.EVENT_TYPES
    assert "microsoft_teams" in c.INTEGRATION_PROVIDERS
    assert "zapier" in c.INTEGRATION_PROVIDERS
    assert c.category_for_event("payment.completed") == "billing"
    sig = c.sign_webhook_payload('{"a":1}')
    assert c.verify_webhook_signature('{"a":1}', sig) is True
    assert c.verify_webhook_signature('{"a":1}', "bad") is False


def test_engine_status_unit():
    status = _svc().status()
    assert status["ok"] is True
    assert status["phase"] == 9
    assert status["sprint"] == 8
    assert len(status["engines"]) == 6
    assert all(v == "ready" for v in status["engines"].values())


# --- Automation Engine ---


def test_automation_crud():
    org_id = _seed_org("owner_auto")
    created = _create_rule(org_id, "owner_auto")
    rule = created["automation"]
    assert rule["triggerEvent"] == "ai.job.completed"
    listed = _svc().automation.list(actor_id="owner_auto", organization_id=org_id)
    assert listed["count"] == 1
    updated = _svc().automation.update(
        rule["id"], {"status": "paused", "description": "Paused"}, actor_id="owner_auto"
    )
    assert updated["automation"]["status"] == "paused"
    deleted = _svc().automation.delete(rule["id"], actor_id="owner_auto")
    assert deleted["status"] == "archived"


def test_automation_modes():
    org_id = _seed_org("owner_modes")
    for mode in ("manual", "multi_step", "ai_workflow", "background", "queue"):
        created = _create_rule(
            org_id,
            "owner_modes",
            name=f"{mode} rule",
            mode=mode,
            triggerEvent="" if mode != "event" else "custom.event",
            actions=[{"type": "log"}, {"type": "notify"}]
            if mode == "multi_step"
            else [{"type": "notify"}],
        )
        assert created["automation"]["mode"] == mode


def test_conditional_automation():
    org_id = _seed_org("owner_cond")
    rule = _create_rule(
        org_id,
        "owner_cond",
        mode="conditional",
        triggerEvent="asset.uploaded",
        conditions={"requirePayloadKey": "assetId"},
        actions=[{"type": "notify"}],
    )["automation"]
    # Publish without required key → skipped
    result = _svc().publish_and_process(
        {
            "organizationId": org_id,
            "eventType": "asset.uploaded",
            "payload": {},
        },
        actor_id="owner_cond",
    )
    assert result["processing"]["matchedRules"] == 1
    assert result["processing"]["executions"][0]["status"] == "skipped"
    # With key → completed
    result = _svc().publish_and_process(
        {
            "organizationId": org_id,
            "eventType": "asset.uploaded",
            "payload": {"assetId": "a1"},
        },
        actor_id="owner_cond",
    )
    assert result["processing"]["executions"][0]["status"] == "completed"


# --- Event Bus ---


def test_event_publish_and_history():
    org_id = _seed_org("owner_evt")
    _create_rule(org_id, "owner_evt")
    published = _svc().publish_and_process(
        {
            "organizationId": org_id,
            "eventType": "ai.job.completed",
            "payload": {"jobId": "j1"},
        },
        actor_id="owner_evt",
    )
    assert published["event"]["category"] == "ai_generation"
    assert published["processing"]["matchedRules"] == 1
    history = _svc().bus.history(actor_id="owner_evt", organization_id=org_id)
    assert history["count"] >= 1
    assert any(l["action"] == "published" for l in history["logs"])


def test_event_signature_validation():
    org_id = _seed_org("owner_sig")
    catalog = _catalog()
    body = {"jobId": "x"}
    canonical = json.dumps(
        {
            "eventType": "ai.job.completed",
            "organizationId": org_id,
            "payload": body,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    sig = catalog.sign_webhook_payload(canonical, "mysecret")
    ok = _svc().bus.publish(
        {
            "organizationId": org_id,
            "eventType": "ai.job.completed",
            "payload": body,
            "signature": sig,
            "signingSecret": "mysecret",
        },
        actor_id="owner_sig",
    )
    assert ok["ok"] is True
    try:
        _svc().bus.publish(
            {
                "organizationId": org_id,
                "eventType": "ai.job.completed",
                "payload": body,
                "signature": "deadbeef",
                "signingSecret": "mysecret",
            },
            actor_id="owner_sig",
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_all_trigger_events():
    org_id = _seed_org("owner_trig")
    triggers = [
        "user.registered",
        "project.created",
        "asset.uploaded",
        "ai.job.completed",
        "payment.completed",
        "subscription.renewed",
        "marketplace.purchase",
        "webhook.received",
        "custom.event",
    ]
    for event_type in triggers:
        _create_rule(
            org_id,
            "owner_trig",
            name=f"Rule {event_type}",
            triggerEvent=event_type,
        )
        result = _svc().publish_and_process(
            {
                "organizationId": org_id,
                "eventType": event_type,
                "payload": {"ok": True},
            },
            actor_id="owner_trig",
        )
        assert result["processing"]["matchedRules"] >= 1


# --- Integration Hub ---


def test_integration_connect_and_status():
    org_id = _seed_org("owner_int")
    conn = _svc().hub.connect(
        {
            "organizationId": org_id,
            "provider": "slack",
            "credentialsRef": "vault://slack/1",
        },
        actor_id="owner_int",
    )["connection"]
    assert conn["provider"] == "slack"
    assert "credentialsRef" not in conn
    status = _svc().hub.status(actor_id="owner_int", organization_id=org_id)
    assert status["connected"] == 1
    assert status["byProvider"]["slack"] == 1


def test_all_integration_providers():
    org_id = _seed_org("owner_prov")
    for provider in _catalog().INTEGRATION_PROVIDERS:
        conn = _svc().hub.connect(
            {
                "organizationId": org_id,
                "provider": provider,
                "credentialsRef": f"vault://{provider}/1",
            },
            actor_id="owner_prov",
        )["connection"]
        assert conn["provider"] == provider


def test_webhook_integration_delivery():
    org_id = _seed_org("owner_wh")
    conn = _svc().hub.connect(
        {
            "organizationId": org_id,
            "provider": "webhook",
            "credentialsRef": "vault://webhook/1",
            "webhookSecret": "whsec",
        },
        actor_id="owner_wh",
    )
    assert conn.get("webhookSecret") == "whsec"
    rule = _create_rule(
        org_id,
        "owner_wh",
        name="Deliver Webhook",
        triggerEvent="payment.completed",
        actions=[{"type": "integration_deliver"}],
        integrationId=conn["connection"]["id"],
    )["automation"]
    result = _svc().publish_and_process(
        {
            "organizationId": org_id,
            "eventType": "payment.completed",
            "payload": {"amount": 89},
        },
        actor_id="owner_wh",
    )
    exec_result = result["processing"]["executions"][0]
    assert exec_result["status"] == "completed"
    assert exec_result["results"][0]["output"]["delivered"] is True


# --- Scheduler ---


def test_scheduled_automation_tick():
    org_id = _seed_org("owner_sch")
    rule = _create_rule(
        org_id,
        "owner_sch",
        name="Daily Digest",
        mode="scheduled",
        triggerEvent="",
        actions=[{"type": "notify"}],
    )["automation"]
    job = _svc().scheduler.schedule(
        {
            "organizationId": org_id,
            "ruleId": rule["id"],
            "kind": "once",
            "delayMinutes": 0,
        },
        actor_id="owner_sch",
    )["schedule"]
    store = sys.modules["app.services.enterprise_automation.store"]
    stored = store.get_schedule(job["id"])
    stored.next_run_at = stored.next_run_at - timedelta(minutes=1)
    store.save_schedule(stored)
    tick = _svc().scheduler.tick(actor_id="owner_sch", organization_id=org_id)
    assert tick["processed"] == 1
    assert tick["executions"][0]["status"] == "completed"


# --- Security ---


def test_security_ownership_and_org_isolation():
    org_a = _seed_org("owner_oa")
    org_b = _seed_org("owner_ob")
    rule = _create_rule(org_a, "owner_oa")["automation"]
    try:
        _svc().automation.update(rule["id"], {"name": "x"}, actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        _svc().automation.list(actor_id="owner_ob", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        _svc().bus.history(actor_id="owner_ob", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


def test_security_workspace_isolation():
    org_id = _seed_org("owner_ws")
    conn = _svc().hub.connect(
        {
            "organizationId": org_id,
            "provider": "github",
            "workspaceId": "ws_a",
            "credentialsRef": "vault://gh/1",
        },
        actor_id="owner_ws",
    )["connection"]
    try:
        _create_rule(
            org_id,
            "owner_ws",
            workspaceId="ws_b",
            integrationId=conn["id"],
            actions=[{"type": "integration_deliver"}],
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_security_audit_logging():
    org_id = _seed_org("owner_aud")
    audit_store = sys.modules["app.services.enterprise_auth.store"]
    _create_rule(org_id, "owner_aud")
    _svc().hub.connect(
        {
            "organizationId": org_id,
            "provider": "discord",
            "credentialsRef": "vault://discord/1",
        },
        actor_id="owner_aud",
    )
    _svc().publish_and_process(
        {
            "organizationId": org_id,
            "eventType": "ai.job.completed",
            "payload": {},
        },
        actor_id="owner_aud",
    )
    actions = {e.event_type for e in audit_store.list_audits(limit=500)}
    assert "enterprise_automation.rule_created" in actions
    assert "enterprise_automation.integration_connected" in actions
    assert "enterprise_automation.event_published" in actions


# --- Integration / full workflow ---


def test_full_event_driven_workflow():
    org_id = _seed_org("owner_full")
    svc = _svc()
    conn = svc.hub.connect(
        {
            "organizationId": org_id,
            "provider": "zapier",
            "credentialsRef": "vault://zapier/1",
        },
        actor_id="owner_full",
    )["connection"]
    rule = svc.automation.create(
        {
            "organizationId": org_id,
            "name": "Purchase Pipeline",
            "mode": "multi_step",
            "triggerEvent": "marketplace.purchase",
            "actions": [
                {"type": "log"},
                {"type": "notify"},
                {"type": "integration_deliver"},
            ],
            "integrationId": conn["id"],
        },
        actor_id="owner_full",
    )["automation"]
    result = svc.publish_and_process(
        {
            "organizationId": org_id,
            "eventType": "marketplace.purchase",
            "payload": {"orderId": "o1"},
        },
        actor_id="owner_full",
    )
    assert result["processing"]["matchedRules"] == 1
    assert len(result["processing"]["executions"][0]["results"]) == 3
    history = svc.bus.history(actor_id="owner_full", organization_id=org_id)
    assert history["count"] >= 1
    status = svc.hub.status(actor_id="owner_full", organization_id=org_id)
    assert status["connected"] == 1
    engine = svc.status()
    assert engine["stats"]["automationRules"] >= 1
    assert engine["stats"]["events"] >= 1
    assert rule["id"]


# --- Performance ---


def test_performance_event_burst():
    org_id = _seed_org("owner_perf")
    _create_rule(
        org_id,
        "owner_perf",
        triggerEvent="webhook.received",
        actions=[{"type": "log"}],
    )
    start = time.perf_counter()
    for i in range(100):
        _svc().publish_and_process(
            {
                "organizationId": org_id,
                "eventType": "webhook.received",
                "payload": {"i": i},
            },
            actor_id="owner_perf",
        )
    elapsed = time.perf_counter() - start
    assert elapsed < 10.0
    metrics = _svc().status()["stats"]
    assert metrics["events"] >= 100
    assert metrics["executions"] >= 100

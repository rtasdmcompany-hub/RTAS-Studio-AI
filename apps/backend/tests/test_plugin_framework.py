"""Phase 9 Sprint 5 — Plugin Framework, Extension SDK & Third-Party Integration tests."""

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
        "plugin_framework",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    pf = sys.modules["app.services.plugin_framework"]
    pf.get_plugin_framework_service = sys.modules[
        "app.services.plugin_framework.service"
    ].get_plugin_framework_service
    pf.reset_engine = sys.modules["app.services.plugin_framework.service"].reset_engine


_bootstrap()


def _pf():
    return sys.modules["app.services.plugin_framework.service"]


def _mt():
    return sys.modules["app.services.multi_tenant.service"]


def _version():
    return sys.modules["app.services.plugin_framework.version"]


def _catalog():
    return sys.modules["app.services.plugin_framework.catalog"]


def _errors():
    return sys.modules["app.services.enterprise_auth.errors"]


def _validation():
    return sys.modules["app.services.multi_tenant.validation"]


def setup_function():
    _bootstrap()
    mod = _pf()
    mod._service = None
    sys.modules["app.services.plugin_framework.store"].reset_store()


def _seed_org(owner: str = "owner_1"):
    mt = _mt().get_multi_tenant_service()
    slug = f"pf-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Plugin Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    return org_id


def _svc():
    return _pf().get_plugin_framework_service()


def _manifest(**overrides):
    base = {
        "name": "AI Upscaler",
        "version": "1.0.0",
        "pluginType": "ai_provider",
        "description": "Enterprise AI upscaling plugin",
        "permissions": ["plugin.read", "plugin.write", "storage.read"],
        "minPlatformVersion": "1.0.0",
        "maxPlatformVersion": "99.99.99",
        "hooks": ["onInstall", "onEnable", "onDisable", "onUninstall"],
    }
    base.update(overrides)
    return base


def _register(org_id: str, actor: str, **overrides):
    manifest = _manifest(**(overrides.pop("manifest_overrides", {})))
    payload = {
        "organizationId": org_id,
        "manifest": manifest,
        "description": manifest.get("description", ""),
    }
    payload.update(overrides)
    return _svc().framework.register(payload, actor_id=actor)


# --- Unit ---


def test_version_unit():
    v = _version()
    assert v.PHASE == 9
    assert v.SPRINT == 5
    assert "Plugin Framework" in v.ENGINE_NAME


def test_catalog_unit():
    c = _catalog()
    assert "ai_provider" in c.PLUGIN_TYPES
    assert "video_processing" in c.PLUGIN_TYPES
    assert "payment" in c.PLUGIN_TYPES
    assert "custom" in c.PLUGIN_TYPES
    assert "google_drive" in c.INTEGRATION_PROVIDERS
    assert "zapier" in c.INTEGRATION_PROVIDERS
    assert "webhook" in c.INTEGRATION_PROVIDERS
    assert "make" in c.INTEGRATION_PROVIDERS
    assert c.is_semver("1.2.3") is True
    assert c.is_semver("1.2") is False
    assert c.slugify("My Great Plugin!") == "my-great-plugin"
    errors = c.validate_manifest({"name": "X", "version": "1.0.0", "pluginType": "ai_provider"})
    assert errors == []
    bad = c.validate_manifest({"version": "x"})
    assert any("name" in e for e in bad)
    assert any("semver" in e for e in bad)
    ok, _ = c.check_compatibility({"minPlatformVersion": "1.0.0"})
    assert ok is True
    bad_c, reason = c.check_compatibility({"minPlatformVersion": "9.0.0"})
    assert bad_c is False
    assert "platform" in reason


def test_signature_unit():
    c = _catalog()
    manifest = _manifest()
    sig = c.compute_signature(manifest, "pub_key")
    assert len(sig) == 64
    assert c.verify_signature(manifest, sig, "pub_key") is True
    assert c.verify_signature(manifest, "deadbeef", "pub_key") is False
    assert c.verify_signature(manifest, "", "pub_key") is False


def test_engine_status_unit():
    status = _svc().status()
    assert status["ok"] is True
    assert status["phase"] == 9
    assert status["sprint"] == 5
    assert len(status["engines"]) == 6
    assert all(v == "ready" for v in status["engines"].values())
    assert status["sdk"]["sandboxReady"] is True
    assert "onInstall" in status["sdk"]["lifecycleHooks"]


# --- SDK Engine ---


def test_sdk_metadata_and_validation():
    sdk = _svc().sdk
    meta = sdk.sdk_metadata()
    assert meta["sdkVersion"] == "1.0.0"
    assert "configSchema" in meta["manifestSchema"]["optional"]
    result = sdk.validate_manifest(_manifest())
    assert result["valid"] is True
    assert result["compatible"] is True
    invalid = sdk.validate_manifest({"name": "Bad", "version": "1", "pluginType": "nope"})
    assert invalid["valid"] is False
    assert len(invalid["errors"]) >= 1


def test_sdk_event_bus():
    org_id = _seed_org("owner_sdk")
    plugin = _register(org_id, "owner_sdk")["plugin"]
    published = _svc().sdk.publish_event(
        {
            "organizationId": org_id,
            "pluginId": plugin["id"],
            "eventType": "custom_hook",
            "channel": "plugin.lifecycle",
            "payload": {"ok": True},
        },
        actor_id="owner_sdk",
    )
    assert published["ok"] is True
    listed = _svc().sdk.list_events(
        actor_id="owner_sdk", organization_id=org_id, plugin_id=plugin["id"]
    )
    assert listed["count"] >= 2  # registered + custom
    # Unknown channel rejected
    try:
        _svc().sdk.publish_event(
            {
                "organizationId": org_id,
                "pluginId": plugin["id"],
                "channel": "unknown.channel",
            },
            actor_id="owner_sdk",
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


# --- Plugin Framework Engine ---


def test_register_get_update_delete():
    org_id = _seed_org("owner_reg")
    created = _register(org_id, "owner_reg")
    plugin = created["plugin"]
    assert plugin["pluginType"] == "ai_provider"
    assert plugin["signatureVerified"] is True
    assert plugin["sandboxReady"] is True

    got = _svc().framework.get(plugin["id"], actor_id="owner_reg")
    assert got["plugin"]["id"] == plugin["id"]
    assert len(got["versions"]) == 1

    updated = _svc().framework.update(
        plugin["id"],
        {"description": "Updated desc", "status": "published"},
        actor_id="owner_reg",
    )
    assert updated["plugin"]["description"] == "Updated desc"
    assert updated["plugin"]["status"] == "published"

    deleted = _svc().framework.delete(plugin["id"], actor_id="owner_reg")
    assert deleted["status"] == "deprecated"


def test_register_rejects_invalid_signature():
    org_id = _seed_org("owner_sig")
    try:
        _register(
            org_id,
            "owner_sig",
            signature="not-a-valid-signature",
            publisherKey="pk",
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "signature" in str(exc).lower()


def test_register_rejects_incompatible_platform():
    org_id = _seed_org("owner_inc")
    try:
        _register(
            org_id,
            "owner_inc",
            manifest_overrides={"minPlatformVersion": "99.0.0"},
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_plugin_versioning():
    org_id = _seed_org("owner_ver")
    plugin = _register(org_id, "owner_ver")["plugin"]
    published = _svc().framework.publish_version(
        plugin["id"],
        {
            "version": "1.1.0",
            "changelog": "Bug fixes",
            "manifest": _manifest(version="1.1.0"),
        },
        actor_id="owner_ver",
    )
    assert published["version"]["version"] == "1.1.0"
    got = _svc().framework.get(plugin["id"], actor_id="owner_ver")
    assert got["plugin"]["currentVersion"] == "1.1.0"
    assert len(got["versions"]) == 2
    # Duplicate version rejected
    try:
        _svc().framework.publish_version(
            plugin["id"], {"version": "1.1.0"}, actor_id="owner_ver"
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_all_plugin_types_supported():
    org_id = _seed_org("owner_types")
    for ptype in _catalog().PLUGIN_TYPES:
        created = _register(
            org_id,
            "owner_types",
            manifest_overrides={
                "name": f"Plugin {ptype}",
                "pluginType": ptype,
                "version": "1.0.0",
            },
        )
        assert created["plugin"]["pluginType"] == ptype


# --- Registry ---


def test_registry_list_filters():
    org_id = _seed_org("owner_list")
    _register(
        org_id, "owner_list",
        manifest_overrides={"name": "Video FX", "pluginType": "video_processing"},
    )
    _register(
        org_id, "owner_list",
        manifest_overrides={"name": "Pay Bridge", "pluginType": "payment"},
    )
    listed = _svc().registry.list(actor_id="owner_list", organization_id=org_id)
    assert listed["count"] == 2
    filtered = _svc().registry.list(
        actor_id="owner_list",
        organization_id=org_id,
        plugin_type="payment",
    )
    assert filtered["count"] == 1
    assert filtered["plugins"][0]["pluginType"] == "payment"


# --- Installation Engine ---


def test_install_enable_disable_uninstall():
    org_id = _seed_org("owner_ins")
    plugin = _register(org_id, "owner_ins")["plugin"]
    installed = _svc().installation.install(
        {
            "organizationId": org_id,
            "pluginId": plugin["id"],
            "config": {"mode": "prod"},
        },
        actor_id="owner_ins",
    )["installation"]
    assert installed["status"] == "enabled"
    assert installed["version"] == "1.0.0"

    disabled = _svc().installation.disable(installed["id"], actor_id="owner_ins")
    assert disabled["installation"]["status"] == "disabled"
    enabled = _svc().installation.enable(installed["id"], actor_id="owner_ins")
    assert enabled["installation"]["status"] == "enabled"

    uninstalled = _svc().installation.uninstall(
        {"organizationId": org_id, "pluginId": plugin["id"]},
        actor_id="owner_ins",
    )
    assert uninstalled["installation"]["status"] == "uninstalled"


def test_install_workspace_isolation():
    org_id = _seed_org("owner_ws")
    plugin = _register(org_id, "owner_ws")["plugin"]
    a = _svc().installation.install(
        {
            "organizationId": org_id,
            "pluginId": plugin["id"],
            "workspaceId": "ws_a",
        },
        actor_id="owner_ws",
    )["installation"]
    b = _svc().installation.install(
        {
            "organizationId": org_id,
            "pluginId": plugin["id"],
            "workspaceId": "ws_b",
        },
        actor_id="owner_ws",
    )["installation"]
    assert a["id"] != b["id"]
    listed_a = _svc().installation.list_installed(
        actor_id="owner_ws", organization_id=org_id, workspace_id="ws_a"
    )
    assert listed_a["count"] == 1
    assert listed_a["installations"][0]["workspaceId"] == "ws_a"


def test_install_rejects_duplicate_and_foreign_org():
    org_a = _seed_org("owner_oa")
    org_b = _seed_org("owner_ob")
    plugin = _register(org_a, "owner_oa")["plugin"]
    _svc().installation.install(
        {"organizationId": org_a, "pluginId": plugin["id"]},
        actor_id="owner_oa",
    )
    try:
        _svc().installation.install(
            {"organizationId": org_a, "pluginId": plugin["id"]},
            actor_id="owner_oa",
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass
    try:
        _svc().installation.install(
            {"organizationId": org_b, "pluginId": plugin["id"]},
            actor_id="owner_ob",
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


def test_cannot_delete_with_active_install():
    org_id = _seed_org("owner_del")
    plugin = _register(org_id, "owner_del")["plugin"]
    _svc().installation.install(
        {"organizationId": org_id, "pluginId": plugin["id"]},
        actor_id="owner_del",
    )
    try:
        _svc().framework.delete(plugin["id"], actor_id="owner_del")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_update_config():
    org_id = _seed_org("owner_cfg")
    plugin = _register(org_id, "owner_cfg")["plugin"]
    installed = _svc().installation.install(
        {
            "organizationId": org_id,
            "pluginId": plugin["id"],
            "config": {"a": 1},
            "secretsRef": "vault://secret/1",
        },
        actor_id="owner_cfg",
    )["installation"]
    updated = _svc().installation.update_config(
        installed["id"],
        {"config": {"a": 2, "b": True}, "secretsRef": "vault://secret/2"},
        actor_id="owner_cfg",
    )
    assert updated["configuration"]["config"]["a"] == 2
    assert "secretsRef" not in updated["configuration"]


# --- Permission Engine ---


def test_permission_isolation():
    org_id = _seed_org("owner_perm")
    plugin = _register(
        org_id,
        "owner_perm",
        manifest_overrides={
            "permissions": ["plugin.read", "storage.write", "events.publish"],
        },
    )["plugin"]
    installed = _svc().installation.install(
        {"organizationId": org_id, "pluginId": plugin["id"]},
        actor_id="owner_perm",
    )["installation"]
    perms = _svc().permissions.list_for_installation(
        installed["id"], actor_id="owner_perm"
    )
    keys = {p["permissionKey"] for p in perms["permissions"]}
    assert keys == {"plugin.read", "storage.write", "events.publish"}
    assert all(p["scope"] == "organization" for p in perms["permissions"])
    allowed = _svc().permissions.check(
        installed["id"], "storage.write", actor_id="owner_perm"
    )
    assert allowed["allowed"] is True
    denied = _svc().permissions.check(
        installed["id"], "network.outbound", actor_id="owner_perm"
    )
    assert denied["allowed"] is False


# --- Third-Party Integration Engine ---


def test_integration_connect_list_disconnect():
    org_id = _seed_org("owner_int")
    connected = _svc().integrations.connect(
        {
            "organizationId": org_id,
            "provider": "slack",
            "displayName": "Ops Slack",
            "credentialsRef": "vault://integrations/slack/1",
            "metadata": {"channel": "#ops"},
        },
        actor_id="owner_int",
    )["connection"]
    assert connected["provider"] == "slack"
    assert connected["status"] == "connected"
    # credentials never exposed
    assert "credentialsRef" not in connected

    listed = _svc().integrations.list(
        actor_id="owner_int", organization_id=org_id
    )
    assert listed["count"] == 1

    logs = _svc().integrations.logs(connected["id"], actor_id="owner_int")
    assert logs["count"] >= 1
    assert logs["logs"][0]["eventType"] == "connected"

    disconnected = _svc().integrations.disconnect(
        connected["id"], actor_id="owner_int"
    )
    assert disconnected["status"] == "disconnected"
    listed_after = _svc().integrations.list(
        actor_id="owner_int", organization_id=org_id
    )
    assert listed_after["count"] == 0


def test_all_integration_providers_supported():
    org_id = _seed_org("owner_prov")
    for provider in _catalog().INTEGRATION_PROVIDERS:
        conn = _svc().integrations.connect(
            {
                "organizationId": org_id,
                "provider": provider,
                "credentialsRef": f"vault://integrations/{provider}/1",
            },
            actor_id="owner_prov",
        )["connection"]
        assert conn["provider"] == provider


def test_integration_requires_credentials_ref():
    org_id = _seed_org("owner_cred")
    try:
        _svc().integrations.connect(
            {"organizationId": org_id, "provider": "github"},
            actor_id="owner_cred",
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


# --- Security ---


def test_security_plugin_ownership():
    org_id = _seed_org("owner_sec")
    plugin = _register(org_id, "owner_sec")["plugin"]
    try:
        _svc().framework.update(
            plugin["id"], {"description": "Stolen"}, actor_id="editor_1"
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        _svc().framework.delete(plugin["id"], actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        _svc().framework.publish_version(
            plugin["id"], {"version": "1.0.1"}, actor_id="editor_1"
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


def test_security_organization_isolation():
    org_a = _seed_org("owner_oa2")
    org_b = _seed_org("owner_ob2")
    plugin = _register(org_a, "owner_oa2")["plugin"]
    try:
        _svc().framework.get(plugin["id"], actor_id="owner_ob2")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        _svc().registry.list(actor_id="owner_ob2", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    listed_b = _svc().registry.list(actor_id="owner_ob2", organization_id=org_b)
    assert listed_b["count"] == 0


def test_security_audit_logging():
    org_id = _seed_org("owner_aud")
    audit_store = sys.modules["app.services.enterprise_auth.store"]
    plugin = _register(org_id, "owner_aud")["plugin"]
    _svc().installation.install(
        {"organizationId": org_id, "pluginId": plugin["id"]},
        actor_id="owner_aud",
    )
    _svc().integrations.connect(
        {
            "organizationId": org_id,
            "provider": "discord",
            "credentialsRef": "vault://discord/1",
        },
        actor_id="owner_aud",
    )
    events = audit_store.list_audits(limit=500)
    actions = {e.event_type for e in events}
    assert "plugin_framework.registered" in actions
    assert "plugin_framework.installed" in actions
    assert "plugin_framework.integration_connected" in actions


# --- Integration (full workflow) ---


def test_full_plugin_framework_workflow():
    """Register -> version -> install -> permissions -> config -> enable/disable -> integrate -> uninstall."""
    org_id = _seed_org("owner_full")
    svc = _svc()
    plugin = _register(
        org_id,
        "owner_full",
        manifest_overrides={
            "name": "Flagship Automation",
            "pluginType": "automation",
            "permissions": ["plugin.read", "events.publish", "config.write"],
        },
    )["plugin"]
    pid = plugin["id"]

    svc.framework.publish_version(
        pid,
        {
            "version": "1.1.0",
            "changelog": "Automation hooks",
            "manifest": _manifest(
                name="Flagship Automation",
                version="1.1.0",
                pluginType="automation",
                permissions=["plugin.read", "events.publish", "config.write"],
            ),
        },
        actor_id="owner_full",
    )

    installed = svc.installation.install(
        {
            "organizationId": org_id,
            "pluginId": pid,
            "version": "1.1.0",
            "config": {"schedule": "daily"},
        },
        actor_id="owner_full",
    )["installation"]
    assert installed["version"] == "1.1.0"

    perms = svc.permissions.list_for_installation(
        installed["id"], actor_id="owner_full"
    )
    assert len(perms["permissions"]) == 3

    svc.installation.update_config(
        installed["id"],
        {"config": {"schedule": "hourly"}},
        actor_id="owner_full",
    )
    svc.installation.disable(installed["id"], actor_id="owner_full")
    svc.installation.enable(installed["id"], actor_id="owner_full")

    conn = svc.integrations.connect(
        {
            "organizationId": org_id,
            "provider": "zapier",
            "credentialsRef": "vault://zapier/1",
            "metadata": {"hookUrl": "https://hooks.zapier.com/x"},
        },
        actor_id="owner_full",
    )["connection"]
    assert conn["provider"] == "zapier"

    events = svc.sdk.list_events(actor_id="owner_full", organization_id=org_id)
    event_types = {e["eventType"] for e in events["events"]}
    assert "registered" in event_types
    assert "installed" in event_types
    assert "enabled" in event_types

    svc.installation.uninstall(
        {"organizationId": org_id, "pluginId": pid},
        actor_id="owner_full",
    )
    svc.framework.delete(pid, actor_id="owner_full")

    status = svc.status()
    assert status["stats"]["plugins"] == 1
    assert status["stats"]["versions"] == 2
    assert status["stats"]["connections"] >= 1


# --- Performance ---


def test_bulk_registry_and_install_performance():
    org_id = _seed_org("owner_perf")
    start = time.perf_counter()
    plugin_ids = []
    for i in range(100):
        created = _register(
            org_id,
            "owner_perf",
            manifest_overrides={
                "name": f"Perf Plugin {i}",
                "pluginType": _catalog().PLUGIN_TYPES[i % len(_catalog().PLUGIN_TYPES)],
                "version": "1.0.0",
            },
        )
        plugin_ids.append(created["plugin"]["id"])
    for pid in plugin_ids[:50]:
        _svc().installation.install(
            {"organizationId": org_id, "pluginId": pid},
            actor_id="owner_perf",
        )
    listed = _svc().registry.list(actor_id="owner_perf", organization_id=org_id)
    installed = _svc().installation.list_installed(
        actor_id="owner_perf", organization_id=org_id
    )
    elapsed = time.perf_counter() - start
    assert elapsed < 15.0
    assert listed["count"] == 100
    assert installed["count"] == 50
    metrics = _svc().status()["stats"]
    assert metrics["avgLatencyMs"] >= 0
    assert metrics["plugins"] == 100

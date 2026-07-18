"""Phase 7 Sprint 9 — Platform Administration & Operations Engine tests."""

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
    mt.get_multi_tenant_service = sys.modules["app.services.multi_tenant.service"].get_multi_tenant_service
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
        "platform_ops",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    po = sys.modules["app.services.platform_ops"]
    po.get_platform_ops_service = sys.modules[
        "app.services.platform_ops.service"
    ].get_platform_ops_service
    po.reset_engine = sys.modules["app.services.platform_ops.service"].reset_engine
    po.get_engine = sys.modules["app.services.platform_ops.service"].get_engine


_bootstrap()

version = sys.modules["app.services.platform_ops.version"]
catalog = sys.modules["app.services.platform_ops.catalog"]
service_mod = sys.modules["app.services.platform_ops.service"]
errors = sys.modules["app.services.enterprise_auth.errors"]
mt_service = sys.modules["app.services.multi_tenant.service"]
store = sys.modules["app.services.platform_ops.store"]

SUPER = "super_admin_1"


def setup_function():
    service_mod.reset_engine()


def _seed_org():
    mt = mt_service.get_multi_tenant_service()
    slug = f"ops-org-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Ops Org", "ownerId": "owner_1", "slug": slug}
    )
    return created["organization"]["id"], created["defaultWorkspace"]["id"]


# --- Unit ---


def test_version_unit():
    assert version.PHASE == 7
    assert version.SPRINT == 9
    assert "Administration" in version.ENGINE_NAME


def test_catalog_unit():
    assert "security" in catalog.SETTING_CATEGORIES
    assert "providers" in catalog.CONFIG_NAMESPACES
    assert any(f["key"] == "ai_generation" for f in catalog.DEFAULT_FEATURE_FLAGS)


def test_status_unit():
    svc = service_mod.get_platform_ops_service()
    status = svc.status()
    assert status["ok"] is True
    assert status["sprint"] == 9
    assert status["engines"]["administration"] == "ready"
    assert status["engines"]["system"] == "ready"
    assert status["engines"]["operations"] == "ready"


# --- Admin / Config ---


def test_platform_and_settings():
    svc = service_mod.get_platform_ops_service()
    _seed_org()
    platform = svc.admin.platform(actor_id=SUPER)
    assert platform["ok"] is True
    assert platform["organizationManagement"]["totalOrganizations"] >= 1
    assert platform["featureFlagManagement"]
    settings = svc.config.get_settings(actor_id=SUPER)
    assert settings["settings"]
    assert settings["configurations"]
    updated = svc.config.update_settings(
        {
            "settings": [
                {"key": "platform.name", "value": "RTAS Studio AI Enterprise"},
                {"key": "security.requireMfa", "value": True},
            ]
        },
        actor_id=SUPER,
    )
    assert updated["count"] == 2
    # sensitive requires confirm
    try:
        svc.config.update_settings(
            {"key": "billing.secretKey", "value": "sk_test", "isSecret": True},
            actor_id=SUPER,
        )
        assert False, "expected ValidationError"
    except Exception as exc:
        assert "confirm" in str(exc).lower() or "sensitive" in str(exc).lower()
    confirmed = svc.config.update_settings(
        {
            "key": "billing.secretKey",
            "value": "sk_test",
            "isSecret": True,
            "confirm": True,
        },
        actor_id=SUPER,
    )
    assert confirmed["count"] == 1
    env = svc.config.validate_environment(actor_id=SUPER)
    assert env["isValid"] is True


def test_feature_flags_and_maintenance():
    svc = service_mod.get_platform_ops_service()
    flags = svc.flags.list(actor_id=SUPER)
    assert flags["count"] >= 3
    toggled = svc.flags.set("maintenance_banner", actor_id=SUPER, enabled=True)
    assert toggled["flag"]["enabled"] is True
    maint = svc.maintenance.enable(
        {"message": "Scheduled upgrade", "status": "active"},
        actor_id=SUPER,
    )
    assert maint["maintenance"]["status"] == "active"
    platform = svc.admin.platform(actor_id=SUPER)
    assert platform["maintenanceMode"]["enabled"] is True
    disabled = svc.maintenance.disable(actor_id=SUPER)
    assert disabled["disabled"] is True


# --- System operations ---


def test_system_ops_cache_restart_logs():
    svc = service_mod.get_platform_ops_service()
    system = svc.system.status(actor_id=SUPER)
    assert system["systemHealth"] in {"healthy", "degraded"}
    assert system["databaseStatus"]["healthy"] is True
    assert system["scheduledJobs"]
    providers = svc.admin.providers(actor_id=SUPER)
    assert "fal" in providers["providers"]
    store.cache_set("tmp", 1)
    cleared = svc.system.clear_cache(actor_id=SUPER)
    assert cleared["cleared"] >= 1
    restarted = svc.system.restart_services(actor_id=SUPER, services=["workers", "cache"])
    assert "workers" in restarted["restarted"]
    logs = svc.system.logs(actor_id=SUPER, limit=50)
    assert logs["count"] >= 1


# --- Security ---


def test_super_admin_security():
    svc = service_mod.get_platform_ops_service()
    try:
        svc.admin.platform(actor_id="random_user")
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    try:
        svc.system.clear_cache(actor_id="owner_1")
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    try:
        svc.config.get_settings(actor_id=None)  # type: ignore[arg-type]
        assert False, "expected UnauthorizedError"
    except (errors.UnauthorizedError, TypeError):
        # require_super_admin(None) -> UnauthorizedError
        pass
    try:
        service_mod.require_super_admin(None)
        assert False, "expected UnauthorizedError"
    except errors.UnauthorizedError:
        pass
    # granting works
    store.add_super_admin("ops_admin_2")
    ok = svc.system.status(actor_id="ops_admin_2")
    assert ok["ok"] is True


def test_observability_and_performance():
    svc = service_mod.get_platform_ops_service()
    _seed_org()
    start = time.perf_counter()
    for _ in range(8):
        svc.admin.platform(actor_id=SUPER)
        svc.system.status(actor_id=SUPER)
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0
    obs = svc.observability()
    assert obs["systemHealth"]
    assert obs["platformHealth"]
    assert obs["activeOrganizations"] >= 1
    assert obs["errors"] == 0

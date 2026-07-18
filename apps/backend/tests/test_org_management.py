"""Phase 7 Sprint 3 — Organization, Workspace & Team Management Engine tests."""

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
        (
            "version",
            "roles",
            "models",
            "validation",
            "store",
            "repository",
            "service",
            "engine",
        ),
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
    ea.require_access = sys.modules[
        "app.services.enterprise_auth.middleware"
    ].require_access

    _load_folder(
        "org_management",
        (
            "version",
            "models",
            "store",
            "security",
            "service",
            "engine",
        ),
    )
    om = sys.modules["app.services.org_management"]
    om.get_org_management_service = sys.modules[
        "app.services.org_management.service"
    ].get_org_management_service
    om.reset_engine = sys.modules["app.services.org_management.service"].reset_engine
    om.PHASE = sys.modules["app.services.org_management.version"].PHASE
    om.SPRINT = sys.modules["app.services.org_management.version"].SPRINT


_bootstrap()

version = sys.modules["app.services.org_management.version"]
service_mod = sys.modules["app.services.org_management.service"]
errors = sys.modules["app.services.enterprise_auth.errors"]
mt_service = sys.modules["app.services.multi_tenant.service"]


def setup_function():
    service_mod.reset_engine()


def _seed():
    svc = service_mod.get_org_management_service()
    slug = f"mgmt-{uuid.uuid4().hex[:8]}"
    created = svc.organizations.create(
        {"name": "Mgmt Org", "ownerId": "owner_1", "slug": slug},
        actor_id="owner_1",
    )
    org_id = created["organization"]["id"]
    ws_id = created["defaultWorkspace"]["id"]
    mt_service.get_multi_tenant_service().add_member(
        {"organizationId": org_id, "userId": "admin_1", "role": "admin"}
    )
    mt_service.get_multi_tenant_service().add_member(
        {"organizationId": org_id, "userId": "editor_1", "role": "editor"}
    )
    return svc, org_id, ws_id


# --- Unit ---


def test_version_unit():
    assert version.PHASE == 7
    assert version.SPRINT == 3
    assert version.ENGINE_VERSION == "1.0.0"


def test_team_roles_unit():
    svc = service_mod.get_org_management_service()
    roles = svc.teams.roles()
    assert "lead" in roles["roles"]
    assert "member" in roles["roles"]
    assert "team.update" in roles["permissions"]["lead"]


def test_status_unit():
    svc = service_mod.get_org_management_service()
    status = svc.status()
    assert status["ok"] is True
    assert status["engines"]["organization"] == "ready"
    assert status["engines"]["workspace"] == "ready"
    assert status["engines"]["team"] == "ready"


# --- Organization ---


def test_organization_update_transfer_settings():
    svc, org_id, _ = _seed()
    updated = svc.organizations.update(
        org_id, {"name": "Renamed Org", "status": "active"}, actor_id="owner_1"
    )
    assert updated["organization"]["name"] == "Renamed Org"
    settings = svc.settings.update_org_settings(
        org_id, {"timezone": "Asia/Karachi", "allowInvites": True}, actor_id="owner_1"
    )
    assert settings["settings"]["timezone"] == "Asia/Karachi"
    transferred = svc.organizations.transfer_ownership(
        org_id, actor_id="owner_1", new_owner_id="admin_1"
    )
    assert transferred["organization"]["ownerId"] == "admin_1"


def test_organization_delete_owner_only():
    svc, org_id, _ = _seed()
    try:
        svc.organizations.delete(org_id, actor_id="admin_1")
        assert False
    except errors.ForbiddenError:
        pass
    deleted = svc.organizations.delete(org_id, actor_id="owner_1")
    assert deleted["deleted"] is True


# --- Workspace ---


def test_workspace_lifecycle():
    svc, org_id, ws_id = _seed()
    created = svc.workspaces.create(
        {"organizationId": org_id, "name": "Post", "slug": "post"},
        actor_id="owner_1",
    )
    wid = created["workspace"]["id"]
    archived = svc.workspaces.archive(wid, actor_id="owner_1")
    assert archived["workspace"]["status"] == "archived"
    members = svc.workspaces.members(ws_id, actor_id="owner_1")
    assert members["ok"] is True
    activity = svc.workspaces.activity(wid, actor_id="owner_1")
    assert activity["count"] >= 1
    deleted = svc.workspaces.delete(wid, actor_id="owner_1")
    assert deleted["deleted"] is True


# --- Team ---


def test_team_assign_remove_roles():
    svc, org_id, ws_id = _seed()
    team = svc.teams.create(
        {
            "organizationId": org_id,
            "workspaceId": ws_id,
            "name": "Directors",
            "slug": "directors",
        },
        actor_id="owner_1",
    )
    tid = team["team"]["id"]
    assigned = svc.teams.assign_member(
        tid, "editor_1", actor_id="owner_1", team_role="lead"
    )
    assert assigned["teamMember"]["teamRole"] == "lead"
    renamed = svc.teams.rename(tid, "Film Directors", actor_id="owner_1")
    assert renamed["team"]["name"] == "Film Directors"
    removed = svc.teams.remove_member(tid, "editor_1", actor_id="owner_1")
    assert removed["removed"] is True
    deleted = svc.teams.delete(tid, actor_id="owner_1")
    assert deleted["deleted"] is True


# --- Members / Invitations ---


def test_member_suspend_reactivate_role():
    svc, org_id, _ = _seed()
    mt = mt_service.get_multi_tenant_service()
    members = mt.list_members(org_id)["members"]
    editor = next(m for m in members if m["userId"] == "editor_1")
    suspended = svc.members.suspend(editor["id"], actor_id="owner_1")
    assert suspended["member"]["status"] == "suspended"
    active = svc.members.reactivate(editor["id"], actor_id="owner_1")
    assert active["member"]["status"] == "active"
    role = svc.members.change_role(editor["id"], "manager", actor_id="owner_1")
    assert role["member"]["roleKey"] == "manager"


def test_invitation_accept_reject():
    svc, org_id, _ = _seed()
    invite = svc.invitations.create(
        {
            "organizationId": org_id,
            "email": "hire@rtas.ai",
            "invitedById": "owner_1",
            "role": "editor",
        },
        actor_id="owner_1",
    )
    token = invite["invite"]["token"]
    # reject path on a second invite
    invite2 = svc.invitations.create(
        {
            "organizationId": org_id,
            "email": "reject@rtas.ai",
            "invitedById": "owner_1",
            "role": "viewer",
        },
        actor_id="owner_1",
    )
    rejected = svc.invitations.reject(invite2["invite"]["token"], actor_id="owner_1")
    assert rejected["invite"]["status"] == "rejected"
    accepted = svc.invitations.accept(token, "new_hire")
    assert accepted["member"]["roleKey"] == "editor"


# --- Permission / Security ---


def test_permission_enforcement_security():
    svc, org_id, ws_id = _seed()
    try:
        svc.workspaces.create(
            {"organizationId": org_id, "name": "Nope", "slug": "nope"},
            actor_id="editor_1",
        )
        assert False
    except errors.ForbiddenError:
        pass
    try:
        svc.organizations.delete(org_id, actor_id="editor_1")
        assert False
    except errors.ForbiddenError:
        pass
    # isolation: editor cannot manage other org
    other = svc.organizations.create(
        {"name": "Other", "ownerId": "other_owner", "slug": f"other-{uuid.uuid4().hex[:6]}"},
        actor_id="other_owner",
    )
    try:
        svc.workspaces.list(other["organization"]["id"], actor_id="editor_1")
        assert False
    except errors.ForbiddenError:
        pass


def test_observability():
    svc, org_id, _ = _seed()
    svc.organizations.update(org_id, {"name": "Obs Org"}, actor_id="owner_1")
    obs = svc.observability()
    assert obs["ok"] is True
    assert obs["organizationCount"] >= 1
    assert obs["apiPerformance"]["calls"] >= 1
    assert "activityLogs" in obs

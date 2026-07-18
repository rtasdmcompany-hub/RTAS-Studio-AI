"""Phase 7 Sprint 1 — Multi-Tenant SaaS Platform Foundation tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MT = ROOT / "app" / "services" / "multi_tenant"

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
        sys.modules["app.services"].__path__ = [str(ROOT / "app" / "services")]


def _load_pkg():
    _ensure_parents("app.services.multi_tenant")
    pkg = type(sys)("app.services.multi_tenant")
    pkg.__path__ = [str(MT)]
    sys.modules["app.services.multi_tenant"] = pkg
    for name in (
        "version",
        "roles",
        "models",
        "validation",
        "store",
        "repository",
        "service",
        "engine",
    ):
        _load(f"app.services.multi_tenant.{name}", MT / f"{name}.py")
    eng = sys.modules["app.services.multi_tenant.engine"]
    ver = sys.modules["app.services.multi_tenant.version"]
    svc = sys.modules["app.services.multi_tenant.service"]
    pkg.ENGINE_NAME = ver.ENGINE_NAME
    pkg.ENGINE_VERSION = ver.ENGINE_VERSION
    pkg.ENGINE_LABEL = ver.ENGINE_LABEL
    pkg.PHASE = ver.PHASE
    pkg.SPRINT = ver.SPRINT
    pkg.get_multi_tenant_service = svc.get_multi_tenant_service
    pkg.get_engine = eng.get_engine
    pkg.reset_engine = eng.reset_engine


_load_pkg()

version = sys.modules["app.services.multi_tenant.version"]
roles = sys.modules["app.services.multi_tenant.roles"]
validation = sys.modules["app.services.multi_tenant.validation"]
repository = sys.modules["app.services.multi_tenant.repository"]
service_mod = sys.modules["app.services.multi_tenant.service"]
engine_mod = sys.modules["app.services.multi_tenant.engine"]


def setup_function():
    engine_mod.reset_engine()


# --- Unit tests ---


def test_version_unit():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 7
    assert version.SPRINT == 1


def test_system_roles_unit():
    assert set(roles.SYSTEM_ROLE_KEYS) == {
        "owner",
        "admin",
        "manager",
        "editor",
        "viewer",
    }
    assert roles.role_has_permission("owner", "org.delete") is True
    assert roles.role_has_permission("viewer", "content.write") is False
    assert roles.role_has_permission("editor", "content.write") is True
    assert roles.role_has_permission("admin", "org.billing") is False


def test_slug_validation_unit():
    assert validation.normalize_slug("My Studio") == "my-studio"
    try:
        validation.normalize_slug("---")
        assert False, "expected ValidationError"
    except validation.ValidationError:
        pass
    try:
        validation.validate_email("not-an-email")
        assert False, "expected ValidationError"
    except validation.ValidationError:
        pass
    assert validation.validate_role_key("Admin") == "admin"


def test_repository_seed_rbac_unit():
    repo = repository.get_repository()
    perms = repo.list_permissions()
    assert len(perms) >= 20
    role_keys = {r.key for r in repo.list_roles()}
    assert role_keys == set(roles.SYSTEM_ROLE_KEYS)


# --- Integration tests ---


def test_create_org_with_default_workspace():
    svc = service_mod.get_multi_tenant_service()
    result = svc.create_organization(
        {"name": "RTAS Labs", "ownerId": "user_owner_1", "plan": "pro"}
    )
    assert result["ok"] is True
    org = result["organization"]
    assert org["ownerId"] == "user_owner_1"
    assert org["slug"] == "rtas-labs"
    assert result["defaultWorkspace"]["slug"] == "default"
    members = svc.list_members(org["id"])
    assert members["count"] == 1
    assert members["members"][0]["roleKey"] == "owner"


def test_one_user_multiple_organizations():
    svc = service_mod.get_multi_tenant_service()
    a = svc.create_organization({"name": "Org A", "ownerId": "u_multi", "slug": "org-a"})
    b = svc.create_organization({"name": "Org B", "ownerId": "u_multi", "slug": "org-b"})
    listed = svc.list_organizations(owner_id="u_multi")
    assert listed["count"] == 2
    ids = {o["id"] for o in listed["organizations"]}
    assert a["organization"]["id"] in ids
    assert b["organization"]["id"] in ids


def test_org_multiple_workspaces_and_members():
    svc = service_mod.get_multi_tenant_service()
    created = svc.create_organization(
        {"name": "Cinema Co", "ownerId": "owner1", "slug": "cinema-co"}
    )
    org_id = created["organization"]["id"]
    ws2 = svc.create_workspace(
        {"organizationId": org_id, "name": "Post", "slug": "post"}
    )
    assert ws2["ok"] is True
    workspaces = svc.list_workspaces(org_id)
    assert workspaces["count"] >= 2

    svc.add_member(
        {
            "organizationId": org_id,
            "userId": "editor1",
            "role": "editor",
            "workspaceId": ws2["workspace"]["id"],
        }
    )
    svc.add_member(
        {"organizationId": org_id, "userId": "viewer1", "role": "viewer"}
    )
    members = svc.list_members(org_id)
    assert members["count"] == 3


def test_teams_and_team_members():
    svc = service_mod.get_multi_tenant_service()
    created = svc.create_organization(
        {"name": "Team Org", "ownerId": "owner_t", "slug": "team-org"}
    )
    org_id = created["organization"]["id"]
    ws_id = created["defaultWorkspace"]["id"]
    svc.add_member(
        {"organizationId": org_id, "userId": "mgr1", "role": "manager"}
    )
    team = svc.create_team(
        {
            "organizationId": org_id,
            "workspaceId": ws_id,
            "name": "Directors",
            "slug": "directors",
        }
    )
    tm = svc.add_team_member(team_id=team["team"]["id"], user_id="mgr1")
    assert tm["ok"] is True
    teams = svc.list_teams(org_id, workspace_id=ws_id)
    assert teams["count"] == 1


def test_invite_accept_flow():
    svc = service_mod.get_multi_tenant_service()
    created = svc.create_organization(
        {"name": "Invite Org", "ownerId": "owner_i", "slug": "invite-org"}
    )
    org_id = created["organization"]["id"]
    invite = svc.create_invite(
        {
            "organizationId": org_id,
            "email": "newhire@rtas.ai",
            "invitedById": "owner_i",
            "role": "editor",
        }
    )
    token = invite["invite"]["token"]
    accepted = svc.accept_invite(token, "user_newhire")
    assert accepted["ok"] is True
    assert accepted["member"]["roleKey"] == "editor"
    assert accepted["invite"]["status"] == "accepted"


def test_permission_check_integration():
    svc = service_mod.get_multi_tenant_service()
    created = svc.create_organization(
        {"name": "Perm Org", "ownerId": "owner_p", "slug": "perm-org"}
    )
    org_id = created["organization"]["id"]
    svc.add_member(
        {"organizationId": org_id, "userId": "viewer_p", "role": "viewer"}
    )
    allowed = svc.check_permission(
        organization_id=org_id, user_id="owner_p", permission="org.delete"
    )
    denied = svc.check_permission(
        organization_id=org_id, user_id="viewer_p", permission="org.delete"
    )
    assert allowed["allowed"] is True
    assert denied["allowed"] is False


def test_status_and_roles_endpoints_payload():
    svc = service_mod.get_multi_tenant_service()
    status = svc.status()
    assert status["ok"] is True
    assert status["phase"] == 7
    assert status["sprint"] == 1
    assert "owner" in status["roles"]
    roles_payload = svc.list_roles()
    assert roles_payload["count"] == 5
    perms = svc.list_permissions()
    assert perms["count"] >= 20


def test_get_organization_aggregate():
    svc = service_mod.get_multi_tenant_service()
    created = svc.create_organization(
        {"name": "Agg Org", "ownerId": "owner_a", "slug": "agg-org"}
    )
    detail = svc.get_organization(created["organization"]["id"])
    assert detail["ok"] is True
    assert len(detail["workspaces"]) >= 1
    assert len(detail["members"]) >= 1

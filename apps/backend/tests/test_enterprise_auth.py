"""Phase 7 Sprint 2 — Enterprise Authentication & Access Control tests."""

from __future__ import annotations

import importlib.util
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MT = ROOT / "app" / "services" / "multi_tenant"
EA = ROOT / "app" / "services" / "enterprise_auth"

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


def _load_mt():
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
    svc = sys.modules["app.services.multi_tenant.service"]
    pkg.get_multi_tenant_service = svc.get_multi_tenant_service
    pkg.reset_engine = eng.reset_engine
    pkg.get_engine = eng.get_engine


def _load_ea():
    _ensure_parents("app.services.enterprise_auth")
    pkg = type(sys)("app.services.enterprise_auth")
    pkg.__path__ = [str(EA)]
    sys.modules["app.services.enterprise_auth"] = pkg
    for name in (
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
    ):
        _load(f"app.services.enterprise_auth.{name}", EA / f"{name}.py")
    eng = sys.modules["app.services.enterprise_auth.engine"]
    svc = sys.modules["app.services.enterprise_auth.service"]
    mid = sys.modules["app.services.enterprise_auth.middleware"]
    ver = sys.modules["app.services.enterprise_auth.version"]
    pkg.ENGINE_NAME = ver.ENGINE_NAME
    pkg.ENGINE_VERSION = ver.ENGINE_VERSION
    pkg.PHASE = ver.PHASE
    pkg.SPRINT = ver.SPRINT
    pkg.get_enterprise_auth_service = svc.get_enterprise_auth_service
    pkg.get_engine = eng.get_engine
    pkg.reset_engine = eng.reset_engine
    pkg.require_access = mid.require_access
    pkg.get_access_middleware = mid.get_access_middleware


_load_mt()
_load_ea()

version = sys.modules["app.services.enterprise_auth.version"]
errors = sys.modules["app.services.enterprise_auth.errors"]
perm_eng = sys.modules["app.services.enterprise_auth.permission_engine"]
sso = sys.modules["app.services.enterprise_auth.sso"]
service_mod = sys.modules["app.services.enterprise_auth.service"]
engine_mod = sys.modules["app.services.enterprise_auth.engine"]
mt_service = sys.modules["app.services.multi_tenant.service"]


def setup_function():
    engine_mod.reset_engine()
    mt_service.reset_engine()


def _seed_org():
    mt = mt_service.get_multi_tenant_service()
    slug = f"auth-org-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Auth Org", "ownerId": "owner_1", "slug": slug}
    )
    org_id = created["organization"]["id"]
    ws_id = created["defaultWorkspace"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "admin_1", "role": "admin"})
    mt.add_member({"organizationId": org_id, "userId": "mgr_1", "role": "manager"})
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    mt.add_member({"organizationId": org_id, "userId": "viewer_1", "role": "viewer"})
    team = mt.create_team(
        {"organizationId": org_id, "workspaceId": ws_id, "name": "Core", "slug": "core"}
    )
    mt.add_team_member(team_id=team["team"]["id"], user_id="mgr_1")
    return org_id, ws_id, team["team"]["id"]


# --- Unit ---


def test_version_unit():
    assert version.PHASE == 7
    assert version.SPRINT == 2
    assert version.ENGINE_VERSION == "1.0.0"


def test_permission_engine_roles_unit():
    eng = perm_eng.get_permission_engine()
    assert eng.is_owner("owner")
    assert eng.can_manage_members("admin")
    assert eng.can_manage_workspaces("admin")
    assert eng.can_manage_projects("manager")
    assert eng.can_write("editor")
    assert eng.is_read_only("viewer")
    assert eng.can("viewer", "content.write") is False
    assert eng.can("owner", "org.delete") is True
    catalog = eng.catalog()
    assert "owner" in catalog["roles"]
    assert len(catalog["roles"]) == 5


def test_sso_ready_unit():
    providers = sso.list_sso_providers()
    assert providers["ssoReady"] is True
    assert providers["count"] >= 3
    begin = sso.begin_sso_login(provider_key="oidc_generic", organization_id="org_x")
    assert begin["ok"] is True
    assert begin["ready"] is True


# --- Integration ---


def test_organization_access():
    svc = service_mod.get_enterprise_auth_service()
    org_id, _, _ = _seed_org()
    ok = svc.validate_organization(
        {"organizationId": org_id, "userId": "owner_1"}
    )
    assert ok["ok"] is True
    assert ok["isOwner"] is True
    try:
        svc.validate_organization(
            {"organizationId": org_id, "userId": "stranger"}
        )
        assert False, "expected AccessError"
    except errors.ForbiddenError:
        pass


def test_workspace_access():
    svc = service_mod.get_enterprise_auth_service()
    org_id, ws_id, _ = _seed_org()
    ok = svc.validate_workspace(
        {
            "organizationId": org_id,
            "workspaceId": ws_id,
            "userId": "editor_1",
        }
    )
    assert ok["ok"] is True
    try:
        svc.validate_workspace(
            {
                "organizationId": org_id,
                "workspaceId": "ws_missing",
                "userId": "editor_1",
            }
        )
        assert False
    except errors.NotFoundError:
        pass


def test_role_and_permission_validation():
    svc = service_mod.get_enterprise_auth_service()
    org_id, _, _ = _seed_org()
    owner = svc.check_permission(
        {
            "userId": "owner_1",
            "organizationId": org_id,
            "action": "org.delete",
        }
    )
    viewer = svc.check_permission(
        {
            "userId": "viewer_1",
            "organizationId": org_id,
            "action": "content.write",
        }
    )
    editor = svc.check_permission(
        {
            "userId": "editor_1",
            "organizationId": org_id,
            "action": "content.write",
        }
    )
    assert owner["allowed"] is True
    assert viewer["allowed"] is False
    assert editor["allowed"] is True
    assert viewer["capabilities"]["isReadOnly"] is True


def test_invitation_acceptance():
    svc = service_mod.get_enterprise_auth_service()
    mt = mt_service.get_multi_tenant_service()
    org_id, _, _ = _seed_org()
    invite = mt.create_invite(
        {
            "organizationId": org_id,
            "email": "new@rtas.ai",
            "invitedById": "owner_1",
            "role": "editor",
        }
    )
    accepted = svc.accept_invite(
        {"token": invite["invite"]["token"], "userId": "new_user"}
    )
    assert accepted["ok"] is True
    assert accepted["member"]["roleKey"] == "editor"
    assert accepted["session"]["organizationId"] == org_id


def test_session_validation():
    svc = service_mod.get_enterprise_auth_service()
    org_id, ws_id, _ = _seed_org()
    created = svc.create_session(
        {
            "userId": "owner_1",
            "organizationId": org_id,
            "workspaceId": ws_id,
        }
    )
    token = created["session"]["token"]
    valid = svc.validate_session(token)
    assert valid["valid"] is True
    revoked = svc.revoke_session(token=token)
    assert revoked["session"]["status"] == "revoked"
    try:
        svc.validate_session(token)
        assert False
    except errors.SessionInvalidError:
        pass


def test_authorize_middleware_integration():
    svc = service_mod.get_enterprise_auth_service()
    org_id, ws_id, team_id = _seed_org()
    sess = svc.create_session(
        {"userId": "admin_1", "organizationId": org_id, "workspaceId": ws_id}
    )
    allowed = svc.authorize(
        {
            "sessionToken": sess["session"]["token"],
            "permission": "workspace.create",
        }
    )
    assert allowed["allowed"] is True
    assert allowed["context"]["roleKey"] == "admin"
    team_ok = svc.validate_team({"teamId": team_id, "userId": "mgr_1"})
    assert team_ok["ok"] is True


def test_audit_logging():
    svc = service_mod.get_enterprise_auth_service()
    org_id, _, _ = _seed_org()
    svc.validate_organization({"organizationId": org_id, "userId": "owner_1"})
    try:
        svc.validate_organization({"organizationId": org_id, "userId": "nope"})
    except errors.AccessError:
        pass
    audits = svc.list_audits(organization_id=org_id, limit=20)
    assert audits["count"] >= 1
    types = {a["eventType"] for a in audits["audits"]}
    assert "org_access_validated" in types or "authorize_denied" in types or len(types) >= 1


# --- Security ---


def test_unauthorized_access_security():
    svc = service_mod.get_enterprise_auth_service()
    org_id, ws_id, _ = _seed_org()
    try:
        svc.authorize(
            {
                "userId": "stranger",
                "organizationId": org_id,
                "permission": "org.read",
            }
        )
        assert False
    except errors.ForbiddenError as exc:
        assert exc.status_code == 403

    try:
        svc.authorize({"permission": "org.read"})
        assert False
    except errors.UnauthorizedError as exc:
        assert exc.status_code == 401

    try:
        svc.authorize(
            {
                "userId": "viewer_1",
                "organizationId": org_id,
                "workspaceId": ws_id,
                "permission": "org.delete",
            }
        )
        assert False
    except errors.ForbiddenError as exc:
        assert exc.status_code == 403


def test_ownership_validation_security():
    svc = service_mod.get_enterprise_auth_service()
    org_id, _, _ = _seed_org()
    ok = svc.validate_ownership({"organizationId": org_id, "userId": "owner_1"})
    assert ok["isOwner"] is True
    try:
        svc.validate_ownership({"organizationId": org_id, "userId": "admin_1"})
        assert False
    except errors.ForbiddenError:
        pass


def test_viewer_cannot_write_security():
    svc = service_mod.get_enterprise_auth_service()
    org_id, _, _ = _seed_org()
    try:
        svc.authorize(
            {
                "userId": "viewer_1",
                "organizationId": org_id,
                "action": "content.write",
            }
        )
        assert False
    except errors.ForbiddenError:
        pass


def test_status_payload():
    svc = service_mod.get_enterprise_auth_service()
    status = svc.status()
    assert status["ok"] is True
    assert status["phase"] == 7
    assert status["sprint"] == 2
    assert status["ssoReady"] is True
    assert "access_middleware" in status["components"]
    assert "audit_logging" in status["components"]

"""Phase 7 Sprint 6 — Notifications, Comments & Activity Engine tests."""

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
        "enterprise_comms",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    ec = sys.modules["app.services.enterprise_comms"]
    ec.get_enterprise_comms_service = sys.modules[
        "app.services.enterprise_comms.service"
    ].get_enterprise_comms_service
    ec.reset_engine = sys.modules["app.services.enterprise_comms.service"].reset_engine
    ec.get_engine = sys.modules["app.services.enterprise_comms.service"].get_engine


_bootstrap()

version = sys.modules["app.services.enterprise_comms.version"]
catalog = sys.modules["app.services.enterprise_comms.catalog"]
service_mod = sys.modules["app.services.enterprise_comms.service"]
errors = sys.modules["app.services.enterprise_auth.errors"]
mt_service = sys.modules["app.services.multi_tenant.service"]


def setup_function():
    service_mod.reset_engine()


def _seed_org():
    mt = mt_service.get_multi_tenant_service()
    slug = f"comms-org-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Comms Org", "ownerId": "owner_1", "slug": slug}
    )
    org_id = created["organization"]["id"]
    ws_id = created["defaultWorkspace"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    mt.add_member({"organizationId": org_id, "userId": "viewer_1", "role": "viewer"})
    return org_id, ws_id


# --- Unit ---


def test_version_unit():
    assert version.PHASE == 7
    assert version.SPRINT == 6
    assert "Notifications" in version.ENGINE_NAME


def test_catalog_unit():
    assert "project_created" in catalog.NOTIFICATION_TYPES
    assert "mention_received" in catalog.NOTIFICATION_TYPES
    assert catalog.normalize_notification_type("ai.job.completed") == "ai_job_completed"
    assert "project" in catalog.RESOURCE_TYPES
    assert "user_login" in catalog.ACTIVITY_CATEGORIES


def test_status_unit():
    svc = service_mod.get_enterprise_comms_service()
    status = svc.status()
    assert status["ok"] is True
    assert status["sprint"] == 6
    assert status["engines"]["notifications"] == "ready"
    assert status["engines"]["activity"] == "ready"
    assert status["engines"]["comments"] == "ready"


# --- Notifications ---


def test_notifications_send_read():
    svc = service_mod.get_enterprise_comms_service()
    org_id, _ = _seed_org()
    sent = svc.notifications.send(
        {
            "organizationId": org_id,
            "recipientId": "editor_1",
            "type": "project_created",
            "title": "Project created",
            "body": "Launch Film",
            "resourceType": "project",
            "resourceId": "proj_1",
        },
        actor_id="owner_1",
    )
    assert sent["ok"] is True
    inbox = svc.notifications.list(actor_id="editor_1", organization_id=org_id)
    assert inbox["count"] >= 1
    assert inbox["unreadCount"] >= 1
    nid = inbox["notifications"][0]["id"]
    marked = svc.notifications.mark_read([nid], actor_id="editor_1")
    assert marked["marked"] == 1
    all_marked = svc.notifications.mark_all_read(actor_id="editor_1", organization_id=org_id)
    assert all_marked["ok"] is True


def test_notification_preferences():
    svc = service_mod.get_enterprise_comms_service()
    org_id, _ = _seed_org()
    prefs = svc.preferences.update(
        {
            "organizationId": org_id,
            "channelInApp": True,
            "mutedTypes": ["billing_event"],
        },
        actor_id="editor_1",
    )
    assert "billing_event" in prefs["preference"]["mutedTypes"]
    skipped = svc.notifications.send(
        {
            "organizationId": org_id,
            "recipientId": "editor_1",
            "type": "billing_event",
            "title": "Invoice",
        },
        actor_id="owner_1",
    )
    assert skipped.get("skipped") is True


# --- Comments / Mentions ---


def test_comments_threaded_mentions():
    svc = service_mod.get_enterprise_comms_service()
    org_id, ws_id = _seed_org()
    created = svc.comments.create(
        {
            "organizationId": org_id,
            "workspaceId": ws_id,
            "resourceType": "project",
            "resourceId": "proj_abc",
            "body": "Please review @user:editor_1 thanks",
            "notifyUserId": "viewer_1",
        },
        actor_id="owner_1",
    )
    assert created["ok"] is True
    cid = created["comment"]["id"]
    assert len(created["mentions"]) >= 1
    reply = svc.comments.create(
        {
            "organizationId": org_id,
            "resourceType": "project",
            "resourceId": "proj_abc",
            "parentId": cid,
            "body": "Looking now",
        },
        actor_id="editor_1",
    )
    assert reply["reply"]["commentId"] == cid
    pinned = svc.comments.update(cid, {"isPinned": True}, actor_id="owner_1")
    assert pinned["comment"]["isPinned"] is True
    reacted = svc.comments.update(cid, {"reaction": "👍"}, actor_id="editor_1")
    assert "👍" in reacted["comment"]["reactions"]
    resolved = svc.comments.update(cid, {"isResolved": True}, actor_id="owner_1")
    assert resolved["comment"]["isResolved"] is True
    listed = svc.comments.list_for_resource(
        "proj_abc", actor_id="owner_1", organization_id=org_id, resource_type="project"
    )
    assert listed["count"] >= 1
    assert listed["comments"][0]["replies"]
    editor_inbox = svc.notifications.list(actor_id="editor_1", organization_id=org_id)
    assert any(n["type"] == "mention_received" for n in editor_inbox["notifications"])


def test_comment_edit_delete_permissions():
    svc = service_mod.get_enterprise_comms_service()
    org_id, _ = _seed_org()
    created = svc.comments.create(
        {
            "organizationId": org_id,
            "resourceType": "asset",
            "resourceId": "asset_1",
            "body": "Original note",
        },
        actor_id="owner_1",
    )
    cid = created["comment"]["id"]
    try:
        svc.comments.update(cid, {"body": "Hack"}, actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    try:
        svc.comments.delete(cid, actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    deleted = svc.comments.delete(cid, actor_id="owner_1")
    assert deleted["deleted"] is True


# --- Activity ---


def test_activity_feed():
    svc = service_mod.get_enterprise_comms_service()
    org_id, ws_id = _seed_org()
    svc.activity.log_login(actor_id="owner_1", organization_id=org_id)
    for category, action, summary in [
        ("project", "project.updated", "Project updated"),
        ("asset", "asset.uploaded", "Asset uploaded"),
        ("ai_generation", "ai.job.completed", "AI job completed"),
        ("export", "export.ready", "Export ready"),
        ("download", "download.available", "Download available"),
        ("team", "member.joined", "Member joined"),
        ("organization", "org.updated", "Org updated"),
        ("workspace", "workspace.updated", "Workspace updated"),
    ]:
        svc.activity.emit(
            {
                "organizationId": org_id,
                "workspaceId": ws_id,
                "category": category,
                "action": action,
                "summary": summary,
            },
            actor_id="owner_1",
        )
    feed = svc.activity.list(actor_id="owner_1", organization_id=org_id, limit=50)
    assert feed["count"] >= 8


# --- Announcements ---


def test_announcements():
    svc = service_mod.get_enterprise_comms_service()
    org_id, _ = _seed_org()
    created = svc.announcements.create(
        {
            "organizationId": org_id,
            "title": "Maintenance Window",
            "body": "Platform upgrades tonight",
            "scope": "organization",
            "isPinned": True,
        },
        actor_id="owner_1",
    )
    assert created["announcement"]["isPinned"] is True
    listed = svc.announcements.list(actor_id="editor_1", organization_id=org_id)
    assert listed["count"] >= 1


# --- Security ---


def test_isolation_and_privacy_security():
    svc = service_mod.get_enterprise_comms_service()
    org_id, ws_id = _seed_org()
    other = mt_service.get_multi_tenant_service().create_organization(
        {"name": "Other", "ownerId": "other_o", "slug": f"other-{uuid.uuid4().hex[:6]}"}
    )
    other_id = other["organization"]["id"]
    sent = svc.notifications.send(
        {
            "organizationId": org_id,
            "recipientId": "editor_1",
            "type": "system_alert",
            "title": "Private",
        },
        actor_id="owner_1",
    )
    nid = sent["notification"]["id"]
    # outsider cannot mark another user's notification
    try:
        svc.notifications.mark_read([nid], actor_id="other_o")
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    # activity org isolation
    try:
        svc.activity.list(actor_id="owner_1", organization_id=other_id)
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    # comment workspace isolation
    try:
        svc.comments.create(
            {
                "organizationId": org_id,
                "workspaceId": "ws_fake",
                "resourceType": "project",
                "resourceId": "p1",
                "body": "Nope",
            },
            actor_id="owner_1",
        )
        assert False, "expected access denial"
    except (errors.ForbiddenError, errors.NotFoundError):
        pass
    # viewer cannot write comments
    try:
        svc.comments.create(
            {
                "organizationId": org_id,
                "workspaceId": ws_id,
                "resourceType": "project",
                "resourceId": "p1",
                "body": "Viewer write",
            },
            actor_id="viewer_1",
        )
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass


def test_observability_and_performance():
    svc = service_mod.get_enterprise_comms_service()
    org_id, _ = _seed_org()
    start = time.perf_counter()
    for i in range(10):
        svc.notifications.send(
            {
                "organizationId": org_id,
                "recipientId": "editor_1",
                "type": "system_alert",
                "title": f"Alert {i}",
            },
            actor_id="owner_1",
        )
        svc.activity.emit(
            {
                "organizationId": org_id,
                "category": "system",
                "action": "ping",
                "summary": f"Ping {i}",
            },
            actor_id="owner_1",
        )
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0
    obs = svc.observability()
    assert obs["notificationsSent"] >= 10
    assert obs["activityEvents"] >= 10
    assert obs["errors"] == 0

"""Phase 7 Sprint 4 — Project Management & Collaboration Engine tests."""

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
        "project_collaboration",
        ("version", "roles", "models", "store", "permissions", "service", "engine"),
    )
    pc = sys.modules["app.services.project_collaboration"]
    pc.get_project_collaboration_service = sys.modules[
        "app.services.project_collaboration.service"
    ].get_project_collaboration_service
    pc.reset_engine = sys.modules["app.services.project_collaboration.service"].reset_engine


_bootstrap()

version = sys.modules["app.services.project_collaboration.version"]
roles = sys.modules["app.services.project_collaboration.roles"]
service_mod = sys.modules["app.services.project_collaboration.service"]
errors = sys.modules["app.services.enterprise_auth.errors"]
mt_service = sys.modules["app.services.multi_tenant.service"]


def setup_function():
    service_mod.reset_engine()


def _seed_org():
    mt = mt_service.get_multi_tenant_service()
    slug = f"proj-org-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Proj Org", "ownerId": "owner_1", "slug": slug}
    )
    org_id = created["organization"]["id"]
    ws_id = created["defaultWorkspace"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    mt.add_member({"organizationId": org_id, "userId": "viewer_1", "role": "viewer"})
    return org_id, ws_id


# --- Unit ---


def test_version_unit():
    assert version.PHASE == 7
    assert version.SPRINT == 4


def test_roles_and_statuses_unit():
    assert "draft" in roles.PROJECT_STATUSES
    assert "archived" in roles.PROJECT_STATUSES
    assert roles.role_has_permission("owner", "project.delete")
    assert not roles.role_has_permission("viewer", "project.update")


def test_status_unit():
    svc = service_mod.get_project_collaboration_service()
    status = svc.status()
    assert status["ok"] is True
    assert status["engines"]["project"] == "ready"
    assert status["engines"]["collaboration"] == "ready"


# --- Project ---


def test_project_lifecycle():
    svc = service_mod.get_project_collaboration_service()
    org_id, ws_id = _seed_org()
    created = svc.projects.create(
        {
            "organizationId": org_id,
            "workspaceId": ws_id,
            "name": "Launch Film",
            "template": "ai_production",
        },
        actor_id="owner_1",
    )
    pid = created["project"]["id"]
    assert created["project"]["status"] in roles.PROJECT_STATUSES
    updated = svc.projects.update(pid, {"status": "in_progress"}, actor_id="owner_1")
    assert updated["project"]["status"] == "in_progress"
    fav = svc.projects.favorite(pid, actor_id="owner_1")
    assert fav["project"]["isFavorite"] is True
    dup = svc.projects.duplicate(pid, actor_id="owner_1")
    assert "Copy" in dup["project"]["name"]
    archived = svc.archive.archive(pid, actor_id="owner_1")
    assert archived["project"]["status"] == "archived"
    restored = svc.archive.restore(pid, actor_id="owner_1")
    assert restored["project"]["status"] == "active"
    deleted = svc.archive.soft_delete(pid, actor_id="owner_1")
    assert deleted["project"]["status"] == "deleted"


def test_templates():
    svc = service_mod.get_project_collaboration_service()
    tpls = svc.projects.templates()
    assert tpls["count"] >= 3
    keys = {t["key"] for t in tpls["templates"]}
    assert "blank" in keys and "ai_production" in keys


# --- Collaboration ---


def test_collaboration_members_notes():
    svc = service_mod.get_project_collaboration_service()
    org_id, _ = _seed_org()
    created = svc.projects.create(
        {"organizationId": org_id, "name": "Collab Proj"}, actor_id="owner_1"
    )
    pid = created["project"]["id"]
    member = svc.collaboration.add_member(
        pid, user_id="editor_1", role_key="editor", actor_id="owner_1"
    )
    assert member["member"]["roleKey"] == "editor"
    note = svc.collaboration.add_note(
        pid, body="Internal note for review", actor_id="editor_1"
    )
    assert note["note"]["isInternal"] is True
    notes = svc.collaboration.list_notes(pid, actor_id="owner_1")
    assert notes["count"] >= 1
    removed = svc.collaboration.remove_member(pid, "editor_1", actor_id="owner_1")
    assert removed["removed"] is True


# --- Timeline / Tasks ---


def test_activity_timeline_and_tasks():
    svc = service_mod.get_project_collaboration_service()
    org_id, _ = _seed_org()
    created = svc.projects.create(
        {"organizationId": org_id, "name": "Timeline Proj"}, actor_id="owner_1"
    )
    pid = created["project"]["id"]
    svc.timeline.emit(
        pid,
        actor_id="owner_1",
        action="asset.uploaded",
        event_type="asset_uploaded",
        summary="Asset uploaded",
    )
    svc.timeline.emit(
        pid,
        actor_id="owner_1",
        action="ai.job.started",
        event_type="ai_job_started",
        summary="AI job started",
    )
    svc.timeline.emit(
        pid,
        actor_id="owner_1",
        action="ai.job.completed",
        event_type="ai_job_completed",
        summary="AI job completed",
    )
    svc.timeline.emit(
        pid,
        actor_id="owner_1",
        action="export.generated",
        event_type="export_generated",
        summary="Export generated",
    )
    activity = svc.timeline.activity(pid, actor_id="owner_1")
    timeline = svc.timeline.timeline(pid, actor_id="owner_1")
    assert activity["count"] >= 4
    assert timeline["count"] >= 4
    task = svc.tasks.assign(
        pid, title="Color grade", actor_id="owner_1", assignee_id="editor_1"
    )
    assert task["task"]["assigneeId"] == "editor_1"
    tasks = svc.tasks.list(pid, actor_id="owner_1")
    assert tasks["count"] == 1


# --- Permission / Security ---


def test_permission_and_isolation_security():
    svc = service_mod.get_project_collaboration_service()
    org_id, _ = _seed_org()
    created = svc.projects.create(
        {"organizationId": org_id, "name": "Sec Proj"}, actor_id="owner_1"
    )
    pid = created["project"]["id"]
    # viewer org member but not project member
    try:
        svc.projects.update(pid, {"name": "Hack"}, actor_id="viewer_1")
        assert False
    except errors.ForbiddenError:
        pass
    # other org isolation
    other = mt_service.get_multi_tenant_service().create_organization(
        {"name": "Other", "ownerId": "other_o", "slug": f"other-{uuid.uuid4().hex[:6]}"}
    )
    try:
        svc.projects.create(
            {"organizationId": other["organization"]["id"], "name": "Nope"},
            actor_id="owner_1",
        )
        assert False
    except errors.ForbiddenError:
        pass
    # ownership delete
    svc.collaboration.add_member(
        pid, user_id="editor_1", role_key="lead", actor_id="owner_1"
    )
    try:
        svc.archive.soft_delete(pid, actor_id="editor_1")
        assert False
    except errors.ForbiddenError:
        pass


def test_observability_and_performance():
    svc = service_mod.get_project_collaboration_service()
    org_id, _ = _seed_org()
    start = time.perf_counter()
    for i in range(5):
        svc.projects.create(
            {"organizationId": org_id, "name": f"Perf {i}", "slug": f"perf-{i}-{uuid.uuid4().hex[:4]}"},
            actor_id="owner_1",
        )
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0
    obs = svc.observability()
    assert obs["totalProjects"] >= 5
    assert obs["apiPerformance"]["calls"] >= 5
    listed = svc.projects.list({"organizationId": org_id}, actor_id="owner_1")
    assert listed["count"] >= 5

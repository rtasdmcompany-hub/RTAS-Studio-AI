"""Phase 7 Sprint 7 — Version Control, Approval & Review Engine tests."""

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
        "version_control",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    vc = sys.modules["app.services.version_control"]
    vc.get_version_control_service = sys.modules[
        "app.services.version_control.service"
    ].get_version_control_service
    vc.reset_engine = sys.modules["app.services.version_control.service"].reset_engine
    vc.get_engine = sys.modules["app.services.version_control.service"].get_engine


_bootstrap()

version = sys.modules["app.services.version_control.version"]
catalog = sys.modules["app.services.version_control.catalog"]
service_mod = sys.modules["app.services.version_control.service"]
errors = sys.modules["app.services.enterprise_auth.errors"]
mt_service = sys.modules["app.services.multi_tenant.service"]


def setup_function():
    service_mod.reset_engine()


def _seed_org():
    mt = mt_service.get_multi_tenant_service()
    slug = f"ver-org-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Version Org", "ownerId": "owner_1", "slug": slug}
    )
    org_id = created["organization"]["id"]
    ws_id = created["defaultWorkspace"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    mt.add_member({"organizationId": org_id, "userId": "viewer_1", "role": "viewer"})
    mt.add_member({"organizationId": org_id, "userId": "manager_1", "role": "manager"})
    return org_id, ws_id


# --- Unit ---


def test_version_unit():
    assert version.PHASE == 7
    assert version.SPRINT == 7
    assert "Version Control" in version.ENGINE_NAME


def test_catalog_unit():
    assert "draft" in catalog.VERSION_STATUSES
    assert "published" in catalog.VERSION_STATUSES
    assert catalog.normalize_status("pending") == "pending_review"
    assert catalog.normalize_change_type("prompts") == "prompt"
    assert catalog.can_transition("draft", "pending_review")


def test_status_unit():
    svc = service_mod.get_version_control_service()
    status = svc.status()
    assert status["ok"] is True
    assert status["sprint"] == 7
    assert status["engines"]["version"] == "ready"
    assert status["engines"]["approval"] == "ready"
    assert status["engines"]["review"] == "ready"


# --- Version / Snapshot / Rollback ---


def test_version_lifecycle_compare_rollback():
    svc = service_mod.get_version_control_service()
    org_id, ws_id = _seed_org()
    pid = f"proj_{uuid.uuid4().hex[:8]}"
    v1 = svc.versions.create(
        {
            "organizationId": org_id,
            "workspaceId": ws_id,
            "projectId": pid,
            "label": "Initial",
            "notes": "first cut",
            "snapshot": {"prompt": "hello", "asset": "a1"},
        },
        actor_id="owner_1",
    )
    assert v1["version"]["versionNumber"] == 1
    assert v1["version"]["isCurrent"] is True
    v2 = svc.versions.create(
        {
            "organizationId": org_id,
            "workspaceId": ws_id,
            "projectId": pid,
            "label": "Revised",
            "snapshot": {"prompt": "hello world", "asset": "a2"},
        },
        actor_id="owner_1",
    )
    assert v2["version"]["versionNumber"] == 2
    listed = svc.versions.list(pid, actor_id="owner_1", organization_id=org_id)
    assert listed["count"] == 2
    cmp = svc.versions.compare(v1["version"]["id"], v2["version"]["id"], actor_id="owner_1")
    assert cmp["diffCount"] >= 1
    dup = svc.versions.duplicate(v1["version"]["id"], actor_id="owner_1")
    assert "Copy" in (dup["version"]["label"] or "")
    snap = svc.snapshots.save(
        v2["version"]["id"],
        {"payload": {"prompt": "snap", "asset": "a2"}},
        actor_id="owner_1",
        name="checkpoint",
    )
    assert snap["snapshot"]["name"] == "checkpoint"
    restored = svc.rollbacks.restore(
        {"versionId": v1["version"]["id"], "createNewVersion": True, "note": "go back"},
        actor_id="owner_1",
    )
    assert restored["restored"] is True
    assert restored["rollback"]["toVersionId"]
    changelog = svc.changes.list(pid, actor_id="owner_1", organization_id=org_id)
    assert changelog["count"] >= 1
    assert any(c["changeType"] == "rollback" for c in changelog["changelog"])


# --- Review / Approval ---


def test_review_approve_reject_history():
    svc = service_mod.get_version_control_service()
    org_id, ws_id = _seed_org()
    pid = f"proj_{uuid.uuid4().hex[:8]}"
    ver = svc.versions.create(
        {
            "organizationId": org_id,
            "workspaceId": ws_id,
            "projectId": pid,
            "snapshot": {"prompt": "review me"},
        },
        actor_id="owner_1",
    )
    review = svc.reviews.create(
        {
            "organizationId": org_id,
            "workspaceId": ws_id,
            "projectId": pid,
            "versionId": ver["version"]["id"],
            "reviewType": "team",
            "assigneeId": "manager_1",
            "summary": "Please approve",
            "comment": "Looks almost ready",
        },
        actor_id="owner_1",
    )
    assert review["review"]["status"] == "pending_review"
    assert review["approval"]["id"]
    approved = svc.reviews.approve(
        {"reviewId": review["review"]["id"], "notes": "LGTM"},
        actor_id="manager_1",
    )
    assert approved["review"]["status"] == "approved"
    assert approved["approval"]["status"] == "approved"

    # reject path on second project version review
    ver2 = svc.versions.create(
        {
            "organizationId": org_id,
            "projectId": pid,
            "snapshot": {"prompt": "bad"},
        },
        actor_id="owner_1",
    )
    review2 = svc.reviews.create(
        {
            "organizationId": org_id,
            "projectId": pid,
            "versionId": ver2["version"]["id"],
            "assigneeId": "manager_1",
            "reviewType": "internal",
        },
        actor_id="owner_1",
    )
    rejected = svc.reviews.reject(
        {"reviewId": review2["review"]["id"], "notes": "Needs work"},
        actor_id="manager_1",
    )
    assert rejected["review"]["status"] == "rejected"
    hist = svc.reviews.history(actor_id="owner_1", organization_id=org_id, project_id=pid)
    assert hist["reviewCount"] >= 2
    assert hist["historyCount"] >= 2


def test_change_tracking_types():
    svc = service_mod.get_version_control_service()
    org_id, _ = _seed_org()
    pid = f"proj_{uuid.uuid4().hex[:8]}"
    for ctype, summary in [
        ("prompt", "Prompt updated"),
        ("asset", "Asset swapped"),
        ("project", "Project renamed"),
        ("ai_output", "AI output refreshed"),
        ("member", "Member added"),
        ("workflow", "Workflow step changed"),
        ("timeline", "Timeline trimmed"),
        ("export", "Export generated"),
    ]:
        svc.changes.track(
            {
                "organizationId": org_id,
                "projectId": pid,
                "changeType": ctype,
                "summary": summary,
            },
            actor_id="owner_1",
        )
    log = svc.changes.list(pid, actor_id="owner_1", organization_id=org_id)
    assert log["count"] >= 8


# --- Security ---


def test_isolation_and_permissions_security():
    svc = service_mod.get_version_control_service()
    org_id, ws_id = _seed_org()
    other = mt_service.get_multi_tenant_service().create_organization(
        {"name": "Other", "ownerId": "other_o", "slug": f"other-{uuid.uuid4().hex[:6]}"}
    )
    other_id = other["organization"]["id"]
    pid = f"proj_{uuid.uuid4().hex[:8]}"
    ver = svc.versions.create(
        {
            "organizationId": org_id,
            "workspaceId": ws_id,
            "projectId": pid,
            "snapshot": {"x": 1},
        },
        actor_id="owner_1",
    )
    # outsider cannot list
    try:
        svc.versions.list(pid, actor_id="other_o", organization_id=org_id)
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    # cannot create into other org
    try:
        svc.versions.create(
            {"organizationId": other_id, "projectId": pid, "snapshot": {}},
            actor_id="owner_1",
        )
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    # viewer cannot create version
    try:
        svc.versions.create(
            {"organizationId": org_id, "projectId": pid, "snapshot": {}},
            actor_id="viewer_1",
        )
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    # editor cannot approve unless assigned
    review = svc.reviews.create(
        {
            "organizationId": org_id,
            "projectId": pid,
            "versionId": ver["version"]["id"],
            "assigneeId": "manager_1",
        },
        actor_id="owner_1",
    )
    try:
        svc.reviews.approve({"reviewId": review["review"]["id"]}, actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    # bad workspace
    try:
        svc.versions.create(
            {
                "organizationId": org_id,
                "workspaceId": "ws_fake",
                "projectId": pid,
                "snapshot": {},
            },
            actor_id="owner_1",
        )
        assert False, "expected access denial"
    except (errors.ForbiddenError, errors.NotFoundError):
        pass


def test_observability_and_performance():
    svc = service_mod.get_version_control_service()
    org_id, _ = _seed_org()
    pid = f"proj_{uuid.uuid4().hex[:8]}"
    start = time.perf_counter()
    for i in range(8):
        svc.versions.create(
            {
                "organizationId": org_id,
                "projectId": pid,
                "label": f"v{i}",
                "snapshot": {"n": i},
            },
            actor_id="owner_1",
        )
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0
    obs = svc.observability()
    assert obs["versionCount"] >= 8
    assert obs["changeHistory"] >= 8
    assert obs["errors"] == 0

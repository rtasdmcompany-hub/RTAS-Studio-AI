"""Project Management & Collaboration Engine — Phase 7 Sprint 4."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.services.enterprise_auth.audit import log_auth_event
from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError
from app.services.enterprise_auth.middleware import require_access
from app.services.multi_tenant.repository import get_repository
from app.services.multi_tenant.validation import ValidationError, normalize_slug, require_non_empty
from app.services.project_collaboration import store
from app.services.project_collaboration.models import (
    CollabProject,
    CollaborationNote,
    ProjectActivity,
    ProjectMember,
    ProjectSettings,
    ProjectTask,
    ProjectTemplate,
    ProjectTimelineEvent,
    new_id,
)
from app.services.project_collaboration.permissions import get_project_permissions_engine
from app.services.project_collaboration.roles import (
    PROJECT_ROLE_KEYS,
    PROJECT_ROLES,
    PROJECT_STATUSES,
    SYSTEM_TEMPLATES,
)
from app.services.project_collaboration.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    MAX_MEMBERS_PER_PROJECT,
    MAX_PROJECTS_PER_ORG,
    PHASE,
    SPRINT,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _slug_from_name(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "project"
    return base[:64]


def _ensure_templates() -> None:
    if store.is_seeded():
        return
    for spec in SYSTEM_TEMPLATES:
        if store.get_template_by_key(spec["key"], organization_id=None) is None:
            store.save_template(
                ProjectTemplate(
                    id=new_id("ptpl_"),
                    key=spec["key"],
                    name=spec["name"],
                    description=spec["description"],
                    organization_id=None,
                    default_status=spec["defaultStatus"],
                    is_system=True,
                    blueprint={"statusFlow": list(PROJECT_STATUSES)},
                )
            )
    store.mark_seeded()


def _record_events(
    project_id: str,
    *,
    actor_id: str,
    action: str,
    event_type: str,
    summary: str,
    detail: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    store.add_activity(
        ProjectActivity(
            id=new_id("pact_"),
            project_id=project_id,
            actor_id=actor_id,
            action=action,
            detail=detail,
            metadata=dict(metadata or {}),
        )
    )
    store.add_timeline(
        ProjectTimelineEvent(
            id=new_id("ptl_"),
            project_id=project_id,
            actor_id=actor_id,
            event_type=event_type,
            summary=summary,
            payload=dict(metadata or {}),
        )
    )
    log_auth_event(
        action,
        actor_id=actor_id,
        success=True,
        detail=summary,
        metadata={"projectId": project_id, **(metadata or {})},
    )


class ProjectManagementEngine:
    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            _ensure_templates()
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            name = require_non_empty(payload.get("name"), "name", max_len=160)
            require_access(
                user_id=actor_id,
                organization_id=org_id,
                workspace_id=payload.get("workspaceId") or payload.get("workspace_id"),
                permission="content.write",
            )
            workspace_id = payload.get("workspaceId") or payload.get("workspace_id")
            if workspace_id:
                ws = get_repository().get_workspace(str(workspace_id))
                if ws is None or ws.organization_id != org_id:
                    raise ForbiddenError("workspace isolation violation")
            slug_raw = payload.get("slug") or _slug_from_name(name)
            slug = normalize_slug(slug_raw)
            if store.get_project_by_slug(org_id, slug):
                raise ValidationError(f"project slug '{slug}' already exists")
            if len(store.list_projects(organization_id=org_id, include_deleted=True)) >= MAX_PROJECTS_PER_ORG:
                raise ValidationError("project limit reached for organization")
            status = str(payload.get("status") or "draft").lower()
            if status not in PROJECT_STATUSES or status in {"archived", "deleted"}:
                status = "draft"
            template_key = payload.get("template") or payload.get("templateKey") or "blank"
            template = store.get_template_by_key(str(template_key), organization_id=org_id)
            owner_id = str(payload.get("ownerId") or payload.get("owner_id") or actor_id)
            project = CollabProject(
                id=new_id("prj_"),
                organization_id=org_id,
                workspace_id=str(workspace_id) if workspace_id else None,
                owner_id=owner_id,
                name=name,
                slug=slug,
                description=(str(payload["description"]) if payload.get("description") else None),
                status=status if not template else template.default_status,
                template_id=template.id if template else None,
                is_shared=bool(payload.get("isShared") or payload.get("is_shared")),
                metadata=dict(payload.get("metadata") or {}),
            )
            store.save_project(project)
            store.save_member(
                ProjectMember(
                    id=new_id("pmem_"),
                    project_id=project.id,
                    user_id=owner_id,
                    role_key="owner",
                )
            )
            store.save_settings(
                ProjectSettings(id=new_id("pset_"), project_id=project.id)
            )
            _record_events(
                project.id,
                actor_id=actor_id,
                action="project.created",
                event_type="project_created",
                summary=f"Project '{project.name}' created",
            )
            return {"ok": True, "project": project.to_dict()}

    def list(self, payload: dict[str, Any] | None = None, *, actor_id: str | None = None) -> dict[str, Any]:
        payload = payload or {}
        org_id = payload.get("organizationId") or payload.get("organization_id")
        if actor_id and org_id:
            require_access(
                user_id=actor_id,
                organization_id=str(org_id),
                permission="content.read",
            )
        items = store.list_projects(
            organization_id=str(org_id) if org_id else None,
            workspace_id=payload.get("workspaceId") or payload.get("workspace_id"),
            owner_id=payload.get("ownerId") or payload.get("owner_id"),
            status=payload.get("status"),
            include_deleted=bool(payload.get("includeDeleted")),
        )
        return {
            "ok": True,
            "count": len(items),
            "projects": [p.to_dict() for p in items],
        }

    def get(self, project_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            access = get_project_permissions_engine().require_project_access(
                project_id=project_id, user_id=actor_id, permission="project.read"
            )
            project = access["project"]
            require_access(
                user_id=actor_id,
                organization_id=project.organization_id,
                workspace_id=project.workspace_id,
                permission="content.read",
            )
            return {
                "ok": True,
                "project": project.to_dict(),
                "members": [m.to_dict() for m in store.list_members(project_id)],
                "settings": (store.get_settings(project_id) or ProjectSettings(
                    id="-", project_id=project_id
                )).to_dict(),
                "roleKey": access["roleKey"],
            }

    def update(self, project_id: str, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            access = get_project_permissions_engine().require_project_access(
                project_id=project_id, user_id=actor_id, permission="project.update"
            )
            project = access["project"]
            if payload.get("name"):
                project.name = require_non_empty(payload["name"], "name", max_len=160)
            if payload.get("description") is not None:
                project.description = str(payload["description"]) or None
            if payload.get("status"):
                status = str(payload["status"]).lower()
                if status not in PROJECT_STATUSES:
                    raise ValidationError(f"status must be one of: {', '.join(PROJECT_STATUSES)}")
                if status == "deleted":
                    raise ValidationError("use delete endpoint to soft-delete")
                if status == "archived":
                    raise ValidationError("use archive endpoint")
                project.status = status
            if payload.get("metadata") is not None:
                if not isinstance(payload["metadata"], dict):
                    raise ValidationError("metadata must be an object")
                project.metadata = dict(payload["metadata"])
            if "isShared" in payload or "is_shared" in payload:
                project.is_shared = bool(payload.get("isShared", payload.get("is_shared")))
            project.updated_at = _now()
            store.save_project(project)
            _record_events(
                project_id,
                actor_id=actor_id,
                action="project.updated",
                event_type="project_updated",
                summary=f"Project '{project.name}' updated",
            )
            return {"ok": True, "project": project.to_dict()}

    def duplicate(self, project_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            access = get_project_permissions_engine().require_project_access(
                project_id=project_id, user_id=actor_id, permission="project.duplicate"
            )
            src = access["project"]
            base_slug = f"{src.slug}-copy"
            slug = base_slug
            n = 2
            while store.get_project_by_slug(src.organization_id, slug):
                slug = f"{base_slug}-{n}"
                n += 1
            return self.create(
                {
                    "organizationId": src.organization_id,
                    "workspaceId": src.workspace_id,
                    "name": f"{src.name} (Copy)",
                    "slug": slug,
                    "description": src.description,
                    "status": "draft",
                    "metadata": dict(src.metadata),
                    "isShared": src.is_shared,
                    "ownerId": actor_id,
                },
                actor_id=actor_id,
            )

    def favorite(self, project_id: str, *, actor_id: str, favorite: bool = True) -> dict[str, Any]:
        with store.timed_op():
            access = get_project_permissions_engine().require_project_access(
                project_id=project_id, user_id=actor_id, permission="project.favorite"
            )
            project = access["project"]
            project.is_favorite = bool(favorite)
            project.updated_at = _now()
            store.save_project(project)
            return {"ok": True, "project": project.to_dict()}

    def templates(self, *, organization_id: str | None = None) -> dict[str, Any]:
        _ensure_templates()
        items = store.list_templates(organization_id=organization_id)
        return {"ok": True, "count": len(items), "templates": [t.to_dict() for t in items]}


class ArchiveEngine:
    def archive(self, project_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            access = get_project_permissions_engine().require_project_access(
                project_id=project_id, user_id=actor_id, permission="project.archive"
            )
            project = access["project"]
            project.status = "archived"
            project.archived_at = _now()
            project.updated_at = _now()
            store.save_project(project)
            _record_events(
                project_id,
                actor_id=actor_id,
                action="project.archived",
                event_type="project_archived",
                summary=f"Project '{project.name}' archived",
            )
            return {"ok": True, "project": project.to_dict()}

    def restore(self, project_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            project = store.get_project(project_id)
            if project is None:
                raise NotFoundError("project not found")
            access = get_project_permissions_engine().require_project_access(
                project_id=project_id, user_id=actor_id, permission="project.restore"
            )
            project = access["project"]
            project.status = "active"
            project.archived_at = None
            project.deleted_at = None
            project.updated_at = _now()
            store.save_project(project)
            _record_events(
                project_id,
                actor_id=actor_id,
                action="project.restored",
                event_type="project_updated",
                summary=f"Project '{project.name}' restored",
            )
            return {"ok": True, "project": project.to_dict()}

    def soft_delete(self, project_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            access = get_project_permissions_engine().require_project_access(
                project_id=project_id, user_id=actor_id, permission="project.delete"
            )
            project = access["project"]
            if project.owner_id != actor_id and access["roleKey"] != "owner":
                raise ForbiddenError("project ownership required to delete")
            project.status = "deleted"
            project.deleted_at = _now()
            project.updated_at = _now()
            store.save_project(project)
            _record_events(
                project_id,
                actor_id=actor_id,
                action="project.deleted",
                event_type="project_updated",
                summary=f"Project '{project.name}' deleted",
            )
            return {"ok": True, "deleted": True, "project": project.to_dict()}


class CollaborationEngine:
    def add_member(
        self,
        project_id: str,
        *,
        user_id: str,
        role_key: str = "contributor",
        actor_id: str,
    ) -> dict[str, Any]:
        with store.timed_op():
            access = get_project_permissions_engine().require_project_access(
                project_id=project_id, user_id=actor_id, permission="member.assign"
            )
            project = access["project"]
            # Must be org member
            org_member = get_repository().get_member_by_org_user(
                project.organization_id, user_id
            )
            if org_member is None:
                raise ForbiddenError("user is not a member of the organization")
            role = role_key.strip().lower()
            if role not in PROJECT_ROLE_KEYS or role == "owner":
                raise ValidationError("invalid project role")
            if len(store.list_members(project_id)) >= MAX_MEMBERS_PER_PROJECT:
                raise ValidationError("project member limit reached")
            existing = store.get_member(project_id, user_id)
            if existing:
                existing.role_key = role
                existing.status = "active"
                existing.updated_at = _now()
                store.save_member(existing)
                member = existing
            else:
                member = ProjectMember(
                    id=new_id("pmem_"),
                    project_id=project_id,
                    user_id=user_id,
                    role_key=role,
                )
                store.save_member(member)
            if not project.is_shared:
                project.is_shared = True
                project.updated_at = _now()
                store.save_project(project)
            _record_events(
                project_id,
                actor_id=actor_id,
                action="member.added",
                event_type="member_added",
                summary=f"Member {user_id} added as {role}",
                detail=user_id,
            )
            return {"ok": True, "member": member.to_dict()}

    def remove_member(self, project_id: str, user_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            access = get_project_permissions_engine().require_project_access(
                project_id=project_id, user_id=actor_id, permission="member.remove"
            )
            project = access["project"]
            if user_id == project.owner_id:
                raise ForbiddenError("cannot remove project owner")
            if not store.delete_member(project_id, user_id):
                raise NotFoundError("project member not found")
            _record_events(
                project_id,
                actor_id=actor_id,
                action="member.removed",
                event_type="member_removed",
                summary=f"Member {user_id} removed",
                detail=user_id,
            )
            return {"ok": True, "removed": True, "userId": user_id}

    def add_note(
        self, project_id: str, *, body: str, actor_id: str, is_internal: bool = True
    ) -> dict[str, Any]:
        with store.timed_op():
            get_project_permissions_engine().require_project_access(
                project_id=project_id, user_id=actor_id, permission="note.write"
            )
            text = require_non_empty(body, "body", max_len=5000)
            note = CollaborationNote(
                id=new_id("pnote_"),
                project_id=project_id,
                author_id=actor_id,
                body=text,
                is_internal=bool(is_internal),
            )
            store.save_note(note)
            return {"ok": True, "note": note.to_dict()}

    def list_notes(self, project_id: str, *, actor_id: str, limit: int = 50) -> dict[str, Any]:
        get_project_permissions_engine().require_project_access(
            project_id=project_id, user_id=actor_id, permission="note.read"
        )
        notes = store.list_notes(project_id, limit=limit)
        return {"ok": True, "count": len(notes), "notes": [n.to_dict() for n in notes]}

    def roles(self) -> dict[str, Any]:
        return {
            "ok": True,
            "roles": PROJECT_ROLES,
            "catalog": get_project_permissions_engine().catalog(),
        }


class ActivityTimelineEngine:
    def activity(self, project_id: str, *, actor_id: str, limit: int = 50) -> dict[str, Any]:
        get_project_permissions_engine().require_project_access(
            project_id=project_id, user_id=actor_id, permission="activity.read"
        )
        items = store.list_activity(project_id, limit=limit)
        return {"ok": True, "count": len(items), "activity": [a.to_dict() for a in items]}

    def timeline(self, project_id: str, *, actor_id: str, limit: int = 50) -> dict[str, Any]:
        get_project_permissions_engine().require_project_access(
            project_id=project_id, user_id=actor_id, permission="activity.read"
        )
        items = store.list_timeline(project_id, limit=limit)
        return {"ok": True, "count": len(items), "timeline": [t.to_dict() for t in items]}

    def emit(
        self,
        project_id: str,
        *,
        actor_id: str,
        action: str,
        event_type: str,
        summary: str,
        detail: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Emit custom timeline events (asset upload, AI job, export, etc.)."""
        get_project_permissions_engine().require_project_access(
            project_id=project_id, user_id=actor_id, permission="project.update"
        )
        _record_events(
            project_id,
            actor_id=actor_id,
            action=action,
            event_type=event_type,
            summary=summary,
            detail=detail,
            metadata=metadata,
        )
        return {"ok": True}


class TaskAssignmentEngine:
    def assign(
        self,
        project_id: str,
        *,
        title: str,
        actor_id: str,
        assignee_id: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        with store.timed_op():
            get_project_permissions_engine().require_project_access(
                project_id=project_id, user_id=actor_id, permission="task.assign"
            )
            task = ProjectTask(
                id=new_id("ptask_"),
                project_id=project_id,
                title=require_non_empty(title, "title", max_len=200),
                description=description,
                assignee_id=assignee_id,
                created_by_id=actor_id,
            )
            store.save_task(task)
            _record_events(
                project_id,
                actor_id=actor_id,
                action="task.assigned",
                event_type="project_updated",
                summary=f"Task '{task.title}' assigned",
                detail=assignee_id,
            )
            return {"ok": True, "task": task.to_dict()}

    def list(self, project_id: str, *, actor_id: str) -> dict[str, Any]:
        get_project_permissions_engine().require_project_access(
            project_id=project_id, user_id=actor_id, permission="project.read"
        )
        tasks = store.list_tasks(project_id)
        return {"ok": True, "count": len(tasks), "tasks": [t.to_dict() for t in tasks]}

    def update_status(
        self, task_id: str, status: str, *, actor_id: str
    ) -> dict[str, Any]:
        task = store.get_task(task_id)
        if task is None:
            raise NotFoundError("task not found")
        get_project_permissions_engine().require_project_access(
            project_id=task.project_id, user_id=actor_id, permission="task.update"
        )
        task.status = require_non_empty(status, "status", max_len=40).lower()
        task.updated_at = _now()
        store.save_task(task)
        return {"ok": True, "task": task.to_dict()}


class ProjectCollaborationService:
    def __init__(self) -> None:
        self.projects = ProjectManagementEngine()
        self.collaboration = CollaborationEngine()
        self.timeline = ActivityTimelineEngine()
        self.tasks = TaskAssignmentEngine()
        self.archive = ArchiveEngine()
        self.permissions = get_project_permissions_engine()

    def status(self) -> dict[str, Any]:
        _ensure_templates()
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "modules": [
                "project_management_engine",
                "collaboration_engine",
                "project_permissions_engine",
                "activity_timeline_engine",
                "task_assignment_engine",
                "project_archive_engine",
            ],
            "statuses": list(PROJECT_STATUSES),
            "roles": list(PROJECT_ROLE_KEYS),
            "stats": store.metrics(),
            "engines": {
                "project": "ready",
                "collaboration": "ready",
                "permissions": "ready",
                "timeline": "ready",
                "tasks": "ready",
                "archive": "ready",
            },
        }

    def observability(self) -> dict[str, Any]:
        m = store.metrics()
        return {
            "ok": True,
            "totalProjects": m["totalProjects"],
            "activeProjects": m["activeProjects"],
            "archivedProjects": m["archivedProjects"],
            "teamActivity": m["activityEvents"],
            "collaborationEvents": m["collaborationEvents"],
            "apiPerformance": {
                "calls": m["apiCalls"],
                "avgLatencyMs": m["avgLatencyMs"],
                "p95LatencyMs": m["p95LatencyMs"],
            },
            "errors": m["errors"],
        }


_service: ProjectCollaborationService | None = None


def get_project_collaboration_service() -> ProjectCollaborationService:
    global _service
    _ensure_templates()
    if _service is None:
        _service = ProjectCollaborationService()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    from app.services.multi_tenant.engine import reset_engine as reset_mt
    from app.services.enterprise_auth.engine import reset_engine as reset_ea

    reset_mt()
    reset_ea()
    _service = None


get_engine = get_project_collaboration_service

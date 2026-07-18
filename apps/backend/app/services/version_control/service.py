"""Enterprise Version Control, Approval & Review Engine — Phase 7 Sprint 7."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.services.enterprise_auth.audit import log_auth_event
from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError
from app.services.enterprise_auth.middleware import require_access
from app.services.multi_tenant.repository import get_repository
from app.services.multi_tenant.validation import ValidationError, require_non_empty
from app.services.version_control import store
from app.services.version_control.catalog import (
    APPROVAL_STATUSES,
    CHANGE_TYPES,
    REVIEW_TYPES,
    VERSION_STATUSES,
    can_transition,
    normalize_change_type,
    normalize_status,
)
from app.services.version_control.models import (
    ApprovalHistoryEntry,
    ApprovalRequest,
    ChangeLogEntry,
    ProjectVersion,
    Review,
    ReviewComment,
    RollbackRecord,
    VersionSnapshot,
    new_id,
)
from app.services.version_control.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    MAX_VERSIONS_PER_PROJECT,
    PHASE,
    SPRINT,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _audit(action: str, actor_id: str, detail: str | None = None, **meta: Any) -> None:
    log_auth_event(
        action,
        actor_id=actor_id,
        success=True,
        detail=detail or action,
        metadata=meta,
    )


def _checksum(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _require_org_write(
    *,
    actor_id: str,
    organization_id: str,
    workspace_id: str | None = None,
) -> None:
    require_access(
        user_id=actor_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        permission="content.write",
    )
    if workspace_id:
        ws = get_repository().get_workspace(workspace_id)
        if ws is None or ws.organization_id != organization_id:
            raise ForbiddenError("workspace isolation violation")


def _require_org_read(
    *,
    actor_id: str,
    organization_id: str,
    workspace_id: str | None = None,
) -> None:
    require_access(
        user_id=actor_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        permission="content.read",
    )


def _can_approve(*, actor_id: str, organization_id: str) -> bool:
    member = get_repository().get_member_by_org_user(organization_id, actor_id)
    if member is None:
        return False
    return member.role_key in {"owner", "admin", "manager"}


class ChangeTrackingEngine:
    def track(self, payload: dict[str, Any], *, actor_id: str | None = None) -> dict[str, Any]:
        org_id = require_non_empty(
            payload.get("organizationId") or payload.get("organization_id"),
            "organizationId",
        )
        project_id = require_non_empty(
            payload.get("projectId") or payload.get("project_id"), "projectId"
        )
        try:
            change_type = normalize_change_type(str(payload.get("changeType") or payload.get("type") or "project"))
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        summary = require_non_empty(payload.get("summary"), "summary", max_len=400)
        entry = ChangeLogEntry(
            id=new_id("clog_"),
            organization_id=org_id,
            workspace_id=payload.get("workspaceId") or payload.get("workspace_id"),
            project_id=project_id,
            actor_id=actor_id or payload.get("actorId"),
            change_type=change_type,
            summary=summary,
            before=payload.get("before"),
            after=payload.get("after"),
            metadata=dict(payload.get("metadata") or {}),
            version_id=payload.get("versionId") or payload.get("version_id"),
        )
        store.save_changelog(entry)
        return {"ok": True, "change": entry.to_dict()}

    def list(self, project_id: str, *, actor_id: str, organization_id: str, limit: int = 100) -> dict[str, Any]:
        _require_org_read(actor_id=actor_id, organization_id=organization_id)
        items = store.list_changelog(project_id, limit=limit)
        # org isolation: only return entries for this org
        items = [e for e in items if e.organization_id == organization_id]
        return {"ok": True, "count": len(items), "changelog": [e.to_dict() for e in items]}


class SnapshotEngine:
    def save(
        self,
        version_id: str,
        payload: dict[str, Any],
        *,
        actor_id: str,
        name: str | None = None,
    ) -> dict[str, Any]:
        version = store.get_version(version_id)
        if version is None:
            raise NotFoundError("version not found")
        _require_org_write(
            actor_id=actor_id,
            organization_id=version.organization_id,
            workspace_id=version.workspace_id,
        )
        data = dict(payload.get("payload") or payload.get("snapshot") or payload)
        snap = VersionSnapshot(
            id=new_id("snap_"),
            version_id=version_id,
            name=name or payload.get("name"),
            payload=data,
            checksum=_checksum(data),
            size_bytes=len(json.dumps(data, default=str).encode("utf-8")),
        )
        store.save_snapshot(snap)
        version.snapshot = data
        version.updated_at = _now()
        store.save_version(version)
        return {"ok": True, "snapshot": snap.to_dict(), "version": version.to_dict()}


class VersionControlEngine:
    def __init__(self) -> None:
        self.changes = ChangeTrackingEngine()
        self.snapshots = SnapshotEngine()

    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            project_id = require_non_empty(
                payload.get("projectId") or payload.get("project_id"), "projectId"
            )
            workspace_id = payload.get("workspaceId") or payload.get("workspace_id")
            _require_org_write(
                actor_id=actor_id, organization_id=org_id, workspace_id=workspace_id
            )
            existing = store.list_versions(project_id)
            if existing and existing[0].organization_id != org_id:
                raise ForbiddenError("organization isolation violation")
            if len(existing) >= MAX_VERSIONS_PER_PROJECT:
                raise ValidationError("version limit reached")
            next_num = (existing[0].version_number if existing else 0) + 1
            parent_id = payload.get("parentVersionId") or payload.get("parent_version_id")
            if parent_id and store.get_version(str(parent_id)) is None:
                raise NotFoundError("parent version not found")
            snapshot = dict(payload.get("snapshot") or payload.get("payload") or {})
            make_current = bool(payload.get("isCurrent", payload.get("is_current", True)))
            if make_current:
                store.clear_current(project_id)
            version = ProjectVersion(
                id=new_id("pver_"),
                organization_id=org_id,
                workspace_id=str(workspace_id) if workspace_id else None,
                project_id=project_id,
                version_number=next_num,
                label=payload.get("label"),
                notes=payload.get("notes"),
                status=normalize_status(str(payload.get("status") or "draft")),
                created_by_id=actor_id,
                parent_version_id=str(parent_id) if parent_id else (
                    existing[0].id if existing else None
                ),
                is_current=make_current,
                snapshot=snapshot,
                metadata=dict(payload.get("metadata") or {}),
            )
            store.save_version(version)
            if snapshot:
                store.save_snapshot(
                    VersionSnapshot(
                        id=new_id("snap_"),
                        version_id=version.id,
                        name=payload.get("snapshotName") or f"v{next_num}",
                        payload=snapshot,
                        checksum=_checksum(snapshot),
                        size_bytes=len(json.dumps(snapshot, default=str).encode("utf-8")),
                    )
                )
            self.changes.track(
                {
                    "organizationId": org_id,
                    "workspaceId": workspace_id,
                    "projectId": project_id,
                    "changeType": "version",
                    "summary": f"Created version v{next_num}",
                    "after": {"versionNumber": next_num, "label": version.label},
                    "versionId": version.id,
                },
                actor_id=actor_id,
            )
            _audit("version.created", actor_id, version.id, projectId=project_id)
            return {"ok": True, "version": version.to_dict()}

    def list(self, project_id: str, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_org_read(actor_id=actor_id, organization_id=organization_id)
            items = [
                v
                for v in store.list_versions(project_id)
                if v.organization_id == organization_id
            ]
            return {
                "ok": True,
                "projectId": project_id,
                "count": len(items),
                "versions": [v.to_dict() for v in items],
            }

    def compare(
        self, version_a_id: str, version_b_id: str, *, actor_id: str
    ) -> dict[str, Any]:
        a = store.get_version(version_a_id)
        b = store.get_version(version_b_id)
        if a is None or b is None:
            raise NotFoundError("version not found")
        if a.organization_id != b.organization_id or a.project_id != b.project_id:
            raise ForbiddenError("cannot compare across projects")
        _require_org_read(actor_id=actor_id, organization_id=a.organization_id)
        keys = set(a.snapshot.keys()) | set(b.snapshot.keys())
        diffs = []
        for key in sorted(keys):
            av, bv = a.snapshot.get(key), b.snapshot.get(key)
            if av != bv:
                diffs.append({"field": key, "a": av, "b": bv})
        return {
            "ok": True,
            "versionA": a.to_dict(),
            "versionB": b.to_dict(),
            "diffCount": len(diffs),
            "diffs": diffs,
        }

    def duplicate(self, version_id: str, *, actor_id: str) -> dict[str, Any]:
        src = store.get_version(version_id)
        if src is None:
            raise NotFoundError("version not found")
        return self.create(
            {
                "organizationId": src.organization_id,
                "workspaceId": src.workspace_id,
                "projectId": src.project_id,
                "label": f"{src.label or f'v{src.version_number}'} (Copy)",
                "notes": src.notes,
                "snapshot": dict(src.snapshot),
                "parentVersionId": src.id,
                "metadata": dict(src.metadata),
            },
            actor_id=actor_id,
        )

    def update_notes(
        self, version_id: str, *, actor_id: str, notes: str | None = None, label: str | None = None
    ) -> dict[str, Any]:
        version = store.get_version(version_id)
        if version is None:
            raise NotFoundError("version not found")
        _require_org_write(
            actor_id=actor_id,
            organization_id=version.organization_id,
            workspace_id=version.workspace_id,
        )
        if notes is not None:
            version.notes = notes
        if label is not None:
            version.label = label
        version.updated_at = _now()
        store.save_version(version)
        return {"ok": True, "version": version.to_dict()}


class RollbackEngine:
    def __init__(self) -> None:
        self.versions = VersionControlEngine()
        self.changes = ChangeTrackingEngine()

    def restore(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            version_id = require_non_empty(
                payload.get("versionId") or payload.get("version_id"), "versionId"
            )
            target = store.get_version(version_id)
            if target is None:
                raise NotFoundError("version not found")
            _require_org_write(
                actor_id=actor_id,
                organization_id=target.organization_id,
                workspace_id=target.workspace_id,
            )
            current = store.current_version(target.project_id)
            store.clear_current(target.project_id)
            target.is_current = True
            target.updated_at = _now()
            store.save_version(target)
            # optional: create new version from restored snapshot
            create_new = bool(payload.get("createNewVersion", payload.get("create_new_version")))
            new_version = None
            if create_new:
                created = self.versions.create(
                    {
                        "organizationId": target.organization_id,
                        "workspaceId": target.workspace_id,
                        "projectId": target.project_id,
                        "label": payload.get("label") or f"Restore of v{target.version_number}",
                        "notes": payload.get("notes") or f"Restored from {target.id}",
                        "snapshot": dict(target.snapshot),
                        "parentVersionId": target.id,
                        "isCurrent": True,
                    },
                    actor_id=actor_id,
                )
                new_version = created["version"]
                target.is_current = False
                store.save_version(target)
            record = RollbackRecord(
                id=new_id("rb_"),
                organization_id=target.organization_id,
                workspace_id=target.workspace_id,
                project_id=target.project_id,
                from_version_id=current.id if current else None,
                to_version_id=(new_version["id"] if new_version else target.id),
                actor_id=actor_id,
                note=payload.get("note") or payload.get("notes"),
            )
            store.save_rollback(record)
            store.record_rollback()
            self.changes.track(
                {
                    "organizationId": target.organization_id,
                    "workspaceId": target.workspace_id,
                    "projectId": target.project_id,
                    "changeType": "rollback",
                    "summary": f"Rolled back to v{target.version_number}",
                    "versionId": record.to_version_id,
                },
                actor_id=actor_id,
            )
            _audit("version.restored", actor_id, target.id, projectId=target.project_id)
            return {
                "ok": True,
                "restored": True,
                "version": (new_version or target.to_dict()),
                "rollback": record.to_dict(),
            }

    def rollback(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        payload = {**payload, "createNewVersion": payload.get("createNewVersion", True)}
        return self.restore(payload, actor_id=actor_id)


class ApprovalEngine:
    def __init__(self) -> None:
        self.changes = ChangeTrackingEngine()

    def _history(
        self, approval: ApprovalRequest, *, actor_id: str, to_status: str, note: str | None = None
    ) -> None:
        store.save_approval_history(
            ApprovalHistoryEntry(
                id=new_id("ahist_"),
                approval_id=approval.id,
                actor_id=actor_id,
                from_status=approval.status,
                to_status=to_status,
                note=note,
            )
        )

    def request(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            project_id = require_non_empty(
                payload.get("projectId") or payload.get("project_id"), "projectId"
            )
            workspace_id = payload.get("workspaceId") or payload.get("workspace_id")
            _require_org_write(
                actor_id=actor_id, organization_id=org_id, workspace_id=workspace_id
            )
            version_id = payload.get("versionId") or payload.get("version_id")
            if version_id:
                ver = store.get_version(str(version_id))
                if ver is None or ver.organization_id != org_id or ver.project_id != project_id:
                    raise ForbiddenError("version isolation violation")
            reviewer_id = payload.get("reviewerId") or payload.get("reviewer_id")
            if reviewer_id:
                member = get_repository().get_member_by_org_user(org_id, str(reviewer_id))
                if member is None:
                    raise ForbiddenError("reviewer is not in organization")
            scope = str(payload.get("scope") or "internal").lower()
            if scope not in REVIEW_TYPES:
                raise ValidationError("scope must be internal|team|organization")
            approval = ApprovalRequest(
                id=new_id("appr_"),
                organization_id=org_id,
                workspace_id=str(workspace_id) if workspace_id else None,
                project_id=project_id,
                version_id=str(version_id) if version_id else None,
                requested_by_id=actor_id,
                reviewer_id=str(reviewer_id) if reviewer_id else None,
                status="pending_review",
                scope=scope,
                title=payload.get("title"),
                notes=payload.get("notes"),
            )
            store.save_approval(approval)
            self._history(approval, actor_id=actor_id, to_status="pending_review", note="requested")
            if version_id:
                ver = store.get_version(str(version_id))
                if ver:
                    ver.status = "pending_review"
                    ver.updated_at = _now()
                    store.save_version(ver)
            self.changes.track(
                {
                    "organizationId": org_id,
                    "projectId": project_id,
                    "workspaceId": workspace_id,
                    "changeType": "workflow",
                    "summary": "Approval requested",
                    "versionId": version_id,
                },
                actor_id=actor_id,
            )
            _audit("approval.requested", actor_id, approval.id)
            return {"ok": True, "approval": approval.to_dict()}

    def _decide(
        self,
        payload: dict[str, Any],
        *,
        actor_id: str,
        to_status: str,
    ) -> dict[str, Any]:
        with store.timed_op():
            approval_id = require_non_empty(
                payload.get("approvalId")
                or payload.get("approval_id")
                or payload.get("reviewId")
                or payload.get("id"),
                "approvalId",
            )
            approval = store.get_approval(approval_id)
            if approval is None:
                raise NotFoundError("approval not found")
            _require_org_write(
                actor_id=actor_id,
                organization_id=approval.organization_id,
                workspace_id=approval.workspace_id,
            )
            is_assignee = bool(approval.reviewer_id and approval.reviewer_id == actor_id)
            is_manager = _can_approve(
                actor_id=actor_id, organization_id=approval.organization_id
            )
            if not is_assignee and not is_manager:
                raise ForbiddenError("approval permission denied")
            if not can_transition(approval.status, to_status):
                if not (
                    approval.status in {"pending_review", "under_review", "draft"}
                    and to_status in {"approved", "rejected", "needs_changes", "under_review"}
                ):
                    raise ValidationError(
                        f"cannot transition from {approval.status} to {to_status}"
                    )
            from_status = approval.status
            if from_status == "pending_review" and to_status in {
                "approved",
                "rejected",
                "needs_changes",
            }:
                approval.status = "under_review"
                store.save_approval(approval)
            elapsed = (_now() - approval.created_at).total_seconds()
            store.record_approval_time(max(0.0, elapsed))
            self._history(
                approval,
                actor_id=actor_id,
                to_status=to_status,
                note=payload.get("notes") or payload.get("note"),
            )
            approval.status = to_status
            approval.notes = payload.get("notes") or approval.notes
            approval.decided_at = _now()
            approval.updated_at = _now()
            if not approval.reviewer_id:
                approval.reviewer_id = actor_id
            store.save_approval(approval)
            if approval.version_id:
                ver = store.get_version(approval.version_id)
                if ver:
                    ver.status = to_status
                    ver.updated_at = _now()
                    store.save_version(ver)
            self.changes.track(
                {
                    "organizationId": approval.organization_id,
                    "projectId": approval.project_id,
                    "workspaceId": approval.workspace_id,
                    "changeType": "workflow",
                    "summary": f"Approval {to_status}",
                    "versionId": approval.version_id,
                },
                actor_id=actor_id,
            )
            _audit(f"approval.{to_status}", actor_id, approval.id)
            return {"ok": True, "approval": approval.to_dict(), "fromStatus": from_status}

    def approve(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        return self._decide(payload, actor_id=actor_id, to_status="approved")

    def reject(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        return self._decide(payload, actor_id=actor_id, to_status="rejected")

    def needs_changes(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        return self._decide(payload, actor_id=actor_id, to_status="needs_changes")

    def publish(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        return self._decide(payload, actor_id=actor_id, to_status="published")

    def history(
        self,
        *,
        actor_id: str,
        organization_id: str,
        project_id: str | None = None,
        approval_id: str | None = None,
    ) -> dict[str, Any]:
        _require_org_read(actor_id=actor_id, organization_id=organization_id)
        if approval_id:
            approval = store.get_approval(approval_id)
            if approval is None or approval.organization_id != organization_id:
                raise NotFoundError("approval not found")
            items = store.list_approval_history(approval_id)
        else:
            items = store.list_approval_history(project_id=project_id)
            # filter by org via approvals
            allowed = {
                a.id
                for a in store.list_approvals(organization_id=organization_id, project_id=project_id)
            }
            items = [h for h in items if h.approval_id in allowed]
        return {
            "ok": True,
            "count": len(items),
            "history": [h.to_dict() for h in items],
        }


class ReviewEngine:
    def __init__(self) -> None:
        self.approvals = ApprovalEngine()
        self.changes = ChangeTrackingEngine()

    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            project_id = require_non_empty(
                payload.get("projectId") or payload.get("project_id"), "projectId"
            )
            workspace_id = payload.get("workspaceId") or payload.get("workspace_id")
            _require_org_write(
                actor_id=actor_id, organization_id=org_id, workspace_id=workspace_id
            )
            review_type = str(payload.get("reviewType") or payload.get("type") or "internal").lower()
            if review_type not in REVIEW_TYPES:
                raise ValidationError("reviewType must be internal|team|organization")
            assignee_id = payload.get("assigneeId") or payload.get("assignee_id") or payload.get("reviewerId")
            if assignee_id:
                member = get_repository().get_member_by_org_user(org_id, str(assignee_id))
                if member is None:
                    raise ForbiddenError("assignee is not in organization")
            version_id = payload.get("versionId") or payload.get("version_id")
            # create linked approval request
            approval = self.approvals.request(
                {
                    "organizationId": org_id,
                    "workspaceId": workspace_id,
                    "projectId": project_id,
                    "versionId": version_id,
                    "reviewerId": assignee_id,
                    "scope": review_type,
                    "title": payload.get("title") or "Review request",
                    "notes": payload.get("summary") or payload.get("notes"),
                },
                actor_id=actor_id,
            )["approval"]
            review = Review(
                id=new_id("rev_"),
                organization_id=org_id,
                workspace_id=str(workspace_id) if workspace_id else None,
                project_id=project_id,
                version_id=str(version_id) if version_id else None,
                approval_id=approval["id"],
                created_by_id=actor_id,
                assignee_id=str(assignee_id) if assignee_id else None,
                review_type=review_type,
                status="pending_review",
                summary=payload.get("summary"),
            )
            store.save_review(review)
            comment_body = payload.get("comment") or payload.get("body")
            comments = []
            if comment_body:
                c = ReviewComment(
                    id=new_id("rvc_"),
                    review_id=review.id,
                    author_id=actor_id,
                    body=require_non_empty(comment_body, "comment", max_len=5000),
                )
                store.save_review_comment(c)
                comments.append(c.to_dict())
            if version_id:
                ver = store.get_version(str(version_id))
                if ver and ver.organization_id == org_id:
                    ver.status = "under_review"
                    ver.updated_at = _now()
                    store.save_version(ver)
            self.changes.track(
                {
                    "organizationId": org_id,
                    "projectId": project_id,
                    "workspaceId": workspace_id,
                    "changeType": "review",
                    "summary": f"{review_type} review created",
                    "versionId": version_id,
                },
                actor_id=actor_id,
            )
            _audit("review.created", actor_id, review.id)
            return {
                "ok": True,
                "review": review.to_dict(),
                "approval": approval,
                "comments": comments,
            }

    def approve(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        review_id = payload.get("reviewId") or payload.get("review_id")
        approval_id = payload.get("approvalId") or payload.get("approval_id")
        if review_id and not approval_id:
            review = store.get_review(str(review_id))
            if review is None:
                raise NotFoundError("review not found")
            if not _can_approve(actor_id=actor_id, organization_id=review.organization_id):
                if review.assignee_id and review.assignee_id != actor_id:
                    raise ForbiddenError("review permission denied")
            approval_id = review.approval_id
            result = self.approvals.approve(
                {"approvalId": approval_id, "notes": payload.get("notes")},
                actor_id=actor_id,
            )
            review.status = "approved"
            review.updated_at = _now()
            store.save_review(review)
            return {"ok": True, "review": review.to_dict(), "approval": result["approval"]}
        result = self.approvals.approve(payload, actor_id=actor_id)
        return result

    def reject(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        review_id = payload.get("reviewId") or payload.get("review_id")
        approval_id = payload.get("approvalId") or payload.get("approval_id")
        if review_id and not approval_id:
            review = store.get_review(str(review_id))
            if review is None:
                raise NotFoundError("review not found")
            if not _can_approve(actor_id=actor_id, organization_id=review.organization_id):
                if review.assignee_id and review.assignee_id != actor_id:
                    raise ForbiddenError("review permission denied")
            result = self.approvals.reject(
                {"approvalId": review.approval_id, "notes": payload.get("notes")},
                actor_id=actor_id,
            )
            review.status = "rejected"
            review.updated_at = _now()
            store.save_review(review)
            return {"ok": True, "review": review.to_dict(), "approval": result["approval"]}
        return self.approvals.reject(payload, actor_id=actor_id)

    def add_comment(self, review_id: str, body: str, *, actor_id: str) -> dict[str, Any]:
        review = store.get_review(review_id)
        if review is None:
            raise NotFoundError("review not found")
        _require_org_write(
            actor_id=actor_id,
            organization_id=review.organization_id,
            workspace_id=review.workspace_id,
        )
        comment = ReviewComment(
            id=new_id("rvc_"),
            review_id=review_id,
            author_id=actor_id,
            body=require_non_empty(body, "body", max_len=5000),
        )
        store.save_review_comment(comment)
        return {"ok": True, "comment": comment.to_dict()}

    def history(
        self,
        *,
        actor_id: str,
        organization_id: str,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        _require_org_read(actor_id=actor_id, organization_id=organization_id)
        reviews = store.list_reviews(organization_id=organization_id, project_id=project_id)
        approval_hist = self.approvals.history(
            actor_id=actor_id,
            organization_id=organization_id,
            project_id=project_id,
        )
        return {
            "ok": True,
            "reviews": [r.to_dict() for r in reviews],
            "reviewCount": len(reviews),
            "approvalHistory": approval_hist["history"],
            "historyCount": approval_hist["count"],
        }


class VersionControlService:
    def __init__(self) -> None:
        self.versions = VersionControlEngine()
        self.approvals = ApprovalEngine()
        self.reviews = ReviewEngine()
        self.changes = ChangeTrackingEngine()
        self.snapshots = SnapshotEngine()
        self.rollbacks = RollbackEngine()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "modules": [
                "version_control_engine",
                "approval_engine",
                "review_engine",
                "change_tracking_engine",
                "snapshot_engine",
                "rollback_engine",
            ],
            "statuses": list(VERSION_STATUSES),
            "approvalStatuses": list(APPROVAL_STATUSES),
            "reviewTypes": list(REVIEW_TYPES),
            "changeTypes": list(CHANGE_TYPES),
            "stats": store.metrics(),
            "engines": {
                "version": "ready",
                "approval": "ready",
                "review": "ready",
                "changes": "ready",
                "snapshots": "ready",
                "rollback": "ready",
            },
        }

    def observability(self) -> dict[str, Any]:
        m = store.metrics()
        return {
            "ok": True,
            "versionCount": m["versionCount"],
            "reviewCount": m["reviewCount"],
            "approvalTime": m["approvalTimeSec"],
            "rollbackEvents": m["rollbackEvents"],
            "changeHistory": m["changeHistory"],
            "apiPerformance": {
                "calls": m["apiCalls"],
                "avgLatencyMs": m["avgLatencyMs"],
            },
            "errors": m["errors"],
        }


_service: VersionControlService | None = None


def get_version_control_service() -> VersionControlService:
    global _service
    if _service is None:
        _service = VersionControlService()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    from app.services.multi_tenant.engine import reset_engine as reset_mt
    from app.services.enterprise_auth.engine import reset_engine as reset_ea

    reset_mt()
    reset_ea()
    _service = None


get_engine = get_version_control_service

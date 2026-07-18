"""Organization, Workspace & Team Management Engine — Phase 7 Sprint 3."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.multi_tenant import store as mt_store
from app.services.multi_tenant.repository import get_repository
from app.services.multi_tenant.service import get_multi_tenant_service
from app.services.multi_tenant.validation import (
    ValidationError,
    normalize_slug,
    require_non_empty,
    slug_from_name,
    validate_create_invite,
    validate_create_organization,
    validate_create_team,
    validate_create_workspace,
    validate_plan,
    validate_role_key,
)
from app.services.org_management import store as om_store
from app.services.org_management.models import (
    TEAM_ROLE_PERMISSIONS,
    TEAM_ROLES,
    ActivityLog,
    OrganizationSettings,
    WorkspaceSettings,
    new_id,
)
from app.services.org_management.security import (
    AccessError,
    ForbiddenError,
    NotFoundError,
    assert_team_in_org,
    assert_workspace_isolation,
    audit,
    enforce,
    validate_role,
)
from app.services.org_management.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    SPRINT,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class OrganizationEngine:
    def create(self, payload: dict[str, Any], *, actor_id: str | None = None) -> dict[str, Any]:
        with om_store.timed_op():
            mt = get_multi_tenant_service()
            result = mt.create_organization(payload)
            org_id = result["organization"]["id"]
            SettingsManager().ensure_org_settings(org_id)
            actor = actor_id or result["organization"]["ownerId"]
            self._log(org_id, actor, "organization.created", detail=result["organization"]["slug"])
            audit("organization_created", actor_id=actor, organization_id=org_id, success=True)
            return result

    def list(self, *, owner_id: str | None = None) -> dict[str, Any]:
        return get_multi_tenant_service().list_organizations(owner_id=owner_id)

    def get(self, org_id: str, *, actor_id: str | None = None) -> dict[str, Any]:
        with om_store.timed_op():
            if actor_id:
                enforce(actor_id=actor_id, organization_id=org_id, permission="org.read")
            result = get_multi_tenant_service().get_organization(org_id)
            settings = SettingsManager().get_org_settings(org_id)
            result["settings"] = settings
            return result

    def update(self, org_id: str, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with om_store.timed_op():
            enforce(actor_id=actor_id, organization_id=org_id, permission="org.update")
            repo = get_repository()
            org = repo.get_organization(org_id)
            if org is None:
                raise NotFoundError("organization not found")
            if payload.get("name"):
                org.name = require_non_empty(payload["name"], "name", max_len=120)
            if payload.get("slug"):
                new_slug = normalize_slug(payload["slug"])
                existing = repo.get_organization_by_slug(new_slug)
                if existing and existing.id != org_id:
                    raise ValidationError(f"slug '{new_slug}' is already taken")
                old_slug = org.slug
                org.slug = new_slug
                # refresh slug index
                mt_store._slug_org.pop(old_slug, None)  # type: ignore[attr-defined]
            if payload.get("plan") is not None:
                org.plan = validate_plan(payload.get("plan"))
            if payload.get("status"):
                status = str(payload["status"]).strip().lower()
                if status not in {"active", "suspended", "archived"}:
                    raise ValidationError("status must be active|suspended|archived")
                org.status = status
            if payload.get("metadata") is not None:
                if not isinstance(payload["metadata"], dict):
                    raise ValidationError("metadata must be an object")
                org.metadata = dict(payload["metadata"])
            org.updated_at = _now()
            mt_store.save_organization(org)
            self._log(org_id, actor_id, "organization.updated")
            audit("organization_updated", actor_id=actor_id, organization_id=org_id)
            return {"ok": True, "organization": org.to_dict()}

    def delete(self, org_id: str, *, actor_id: str) -> dict[str, Any]:
        with om_store.timed_op():
            enforce(actor_id=actor_id, organization_id=org_id, require_owner=True)
            if not mt_store.delete_organization(org_id):
                raise NotFoundError("organization not found")
            om_store.delete_org_settings(org_id)
            self._log(org_id, actor_id, "organization.deleted")
            audit("organization_deleted", actor_id=actor_id, organization_id=org_id)
            return {"ok": True, "deleted": True, "organizationId": org_id}

    def transfer_ownership(
        self, org_id: str, *, actor_id: str, new_owner_id: str
    ) -> dict[str, Any]:
        with om_store.timed_op():
            enforce(actor_id=actor_id, organization_id=org_id, require_owner=True)
            repo = get_repository()
            org = repo.get_organization(org_id)
            if org is None:
                raise NotFoundError("organization not found")
            new_owner_id = require_non_empty(new_owner_id, "newOwnerId")
            member = repo.get_member_by_org_user(org_id, new_owner_id)
            if member is None:
                raise ForbiddenError("new owner must be an organization member")
            old_owner = org.owner_id
            org.owner_id = new_owner_id
            org.updated_at = _now()
            mt_store.save_organization(org)
            # Promote new owner role; demote previous to admin
            repo.update_member_role(member.id, "owner")
            old_member = repo.get_member_by_org_user(org_id, old_owner)
            if old_member and old_member.user_id != new_owner_id:
                repo.update_member_role(old_member.id, "admin")
            self._log(
                org_id,
                actor_id,
                "organization.ownership_transferred",
                detail=f"{old_owner}->{new_owner_id}",
            )
            audit(
                "ownership_transferred",
                actor_id=actor_id,
                organization_id=org_id,
                metadata={"from": old_owner, "to": new_owner_id},
            )
            return {"ok": True, "organization": org.to_dict(), "previousOwnerId": old_owner}

    def _log(self, org_id: str, actor_id: str, action: str, detail: str = "") -> None:
        om_store.add_activity(
            ActivityLog(
                id=new_id("act_"),
                organization_id=org_id,
                actor_id=actor_id,
                action=action,
                detail=detail or None,
            )
        )


class WorkspaceEngine:
    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with om_store.timed_op():
            data = validate_create_workspace(payload)
            enforce(
                actor_id=actor_id,
                organization_id=data["organization_id"],
                permission="workspace.create",
            )
            result = get_multi_tenant_service().create_workspace(payload)
            SettingsManager().ensure_ws_settings(result["workspace"]["id"])
            om_store.add_activity(
                ActivityLog(
                    id=new_id("act_"),
                    organization_id=data["organization_id"],
                    workspace_id=result["workspace"]["id"],
                    actor_id=actor_id,
                    action="workspace.created",
                    detail=result["workspace"]["slug"],
                )
            )
            return result

    def list(self, organization_id: str, *, actor_id: str | None = None) -> dict[str, Any]:
        if actor_id:
            enforce(actor_id=actor_id, organization_id=organization_id, permission="workspace.read")
        return get_multi_tenant_service().list_workspaces(organization_id)

    def update(
        self, workspace_id: str, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with om_store.timed_op():
            repo = get_repository()
            ws = repo.get_workspace(workspace_id)
            if ws is None:
                raise NotFoundError("workspace not found")
            enforce(
                actor_id=actor_id,
                organization_id=ws.organization_id,
                workspace_id=workspace_id,
                permission="workspace.update",
            )
            if payload.get("name"):
                ws.name = require_non_empty(payload["name"], "name", max_len=120)
            if payload.get("slug"):
                new_slug = normalize_slug(payload["slug"])
                existing = repo.get_workspace_by_slug(ws.organization_id, new_slug)
                if existing and existing.id != workspace_id:
                    raise ValidationError(f"workspace slug '{new_slug}' already exists")
                mt_store._slug_workspace.pop((ws.organization_id, ws.slug), None)  # type: ignore
                ws.slug = new_slug
            if payload.get("metadata") is not None:
                if not isinstance(payload["metadata"], dict):
                    raise ValidationError("metadata must be an object")
                ws.metadata = dict(payload["metadata"])
            if payload.get("status"):
                status = str(payload["status"]).strip().lower()
                if status not in {"active", "archived"}:
                    raise ValidationError("status must be active|archived")
                ws.status = status
            ws.updated_at = _now()
            mt_store.save_workspace(ws)
            om_store.add_activity(
                ActivityLog(
                    id=new_id("act_"),
                    organization_id=ws.organization_id,
                    workspace_id=ws.id,
                    actor_id=actor_id,
                    action="workspace.updated",
                )
            )
            return {"ok": True, "workspace": ws.to_dict()}

    def archive(self, workspace_id: str, *, actor_id: str) -> dict[str, Any]:
        return self.update(workspace_id, {"status": "archived"}, actor_id=actor_id)

    def delete(self, workspace_id: str, *, actor_id: str) -> dict[str, Any]:
        with om_store.timed_op():
            repo = get_repository()
            ws = repo.get_workspace(workspace_id)
            if ws is None:
                raise NotFoundError("workspace not found")
            enforce(
                actor_id=actor_id,
                organization_id=ws.organization_id,
                workspace_id=workspace_id,
                permission="workspace.delete",
            )
            mt_store.delete_workspace(workspace_id)
            om_store.delete_ws_settings(workspace_id)
            om_store.add_activity(
                ActivityLog(
                    id=new_id("act_"),
                    organization_id=ws.organization_id,
                    workspace_id=workspace_id,
                    actor_id=actor_id,
                    action="workspace.deleted",
                )
            )
            return {"ok": True, "deleted": True, "workspaceId": workspace_id}

    def members(self, workspace_id: str, *, actor_id: str) -> dict[str, Any]:
        repo = get_repository()
        ws = repo.get_workspace(workspace_id)
        if ws is None:
            raise NotFoundError("workspace not found")
        enforce(
            actor_id=actor_id,
            organization_id=ws.organization_id,
            workspace_id=workspace_id,
            permission="member.read",
        )
        members = repo.list_members(ws.organization_id, workspace_id=workspace_id)
        return {
            "ok": True,
            "workspaceId": workspace_id,
            "count": len(members),
            "members": [m.to_dict() for m in members],
        }

    def activity(
        self, workspace_id: str, *, actor_id: str, limit: int = 50
    ) -> dict[str, Any]:
        repo = get_repository()
        ws = repo.get_workspace(workspace_id)
        if ws is None:
            raise NotFoundError("workspace not found")
        enforce(
            actor_id=actor_id,
            organization_id=ws.organization_id,
            workspace_id=workspace_id,
            permission="workspace.read",
        )
        logs = om_store.list_activity(
            organization_id=ws.organization_id, workspace_id=workspace_id, limit=limit
        )
        return {
            "ok": True,
            "workspaceId": workspace_id,
            "count": len(logs),
            "activity": [a.to_dict() for a in logs],
        }


class TeamEngine:
    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with om_store.timed_op():
            data = validate_create_team(payload)
            enforce(
                actor_id=actor_id,
                organization_id=data["organization_id"],
                permission="team.create",
                workspace_id=data.get("workspace_id"),
            )
            result = get_multi_tenant_service().create_team(payload)
            om_store.add_activity(
                ActivityLog(
                    id=new_id("act_"),
                    organization_id=data["organization_id"],
                    workspace_id=data.get("workspace_id"),
                    team_id=result["team"]["id"],
                    actor_id=actor_id,
                    action="team.created",
                    detail=result["team"]["name"],
                )
            )
            return result

    def list(
        self,
        organization_id: str,
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        if actor_id:
            enforce(
                actor_id=actor_id,
                organization_id=organization_id,
                permission="team.read",
                workspace_id=workspace_id,
            )
        return get_multi_tenant_service().list_teams(
            organization_id, workspace_id=workspace_id
        )

    def rename(self, team_id: str, name: str, *, actor_id: str) -> dict[str, Any]:
        return self.update(team_id, {"name": name}, actor_id=actor_id)

    def update(self, team_id: str, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with om_store.timed_op():
            repo = get_repository()
            team = repo.get_team(team_id)
            if team is None:
                raise NotFoundError("team not found")
            enforce(
                actor_id=actor_id,
                organization_id=team.organization_id,
                permission="team.update",
                workspace_id=team.workspace_id,
            )
            if payload.get("name"):
                team.name = require_non_empty(payload["name"], "name", max_len=120)
                if payload.get("slug") is None:
                    # keep slug unless explicitly renamed
                    pass
            if payload.get("slug"):
                new_slug = normalize_slug(payload["slug"])
                existing = repo.get_team_by_slug(team.organization_id, new_slug)
                if existing and existing.id != team_id:
                    raise ValidationError(f"team slug '{new_slug}' already exists")
                mt_store._slug_team.pop((team.organization_id, team.slug), None)  # type: ignore
                team.slug = new_slug
            if payload.get("status"):
                team.status = str(payload["status"]).strip().lower()
            team.updated_at = _now()
            mt_store.save_team(team)
            om_store.add_activity(
                ActivityLog(
                    id=new_id("act_"),
                    organization_id=team.organization_id,
                    workspace_id=team.workspace_id,
                    team_id=team.id,
                    actor_id=actor_id,
                    action="team.updated",
                    detail=team.name,
                )
            )
            return {"ok": True, "team": team.to_dict()}

    def delete(self, team_id: str, *, actor_id: str) -> dict[str, Any]:
        with om_store.timed_op():
            repo = get_repository()
            team = repo.get_team(team_id)
            if team is None:
                raise NotFoundError("team not found")
            enforce(
                actor_id=actor_id,
                organization_id=team.organization_id,
                permission="team.delete",
            )
            mt_store.delete_team(team_id)
            om_store.add_activity(
                ActivityLog(
                    id=new_id("act_"),
                    organization_id=team.organization_id,
                    team_id=team_id,
                    actor_id=actor_id,
                    action="team.deleted",
                )
            )
            return {"ok": True, "deleted": True, "teamId": team_id}

    def assign_member(
        self,
        team_id: str,
        user_id: str,
        *,
        actor_id: str,
        team_role: str = "member",
    ) -> dict[str, Any]:
        with om_store.timed_op():
            repo = get_repository()
            team = repo.get_team(team_id)
            if team is None:
                raise NotFoundError("team not found")
            enforce(
                actor_id=actor_id,
                organization_id=team.organization_id,
                permission="team.update",
            )
            role = team_role.strip().lower()
            if role not in TEAM_ROLES:
                raise ValidationError(f"teamRole must be one of: {', '.join(TEAM_ROLES)}")
            result = get_multi_tenant_service().add_team_member(
                team_id=team_id, user_id=user_id
            )
            tm = mt_store.get_team_member(team_id, user_id)
            if tm:
                tm.team_role = role
                tm.updated_at = _now()
                mt_store.save_team_member(tm)
                result["teamMember"] = tm.to_dict()
            om_store.add_activity(
                ActivityLog(
                    id=new_id("act_"),
                    organization_id=team.organization_id,
                    team_id=team_id,
                    actor_id=actor_id,
                    action="team.member_assigned",
                    detail=f"{user_id}:{role}",
                )
            )
            return result

    def remove_member(self, team_id: str, user_id: str, *, actor_id: str) -> dict[str, Any]:
        with om_store.timed_op():
            repo = get_repository()
            team = repo.get_team(team_id)
            if team is None:
                raise NotFoundError("team not found")
            enforce(
                actor_id=actor_id,
                organization_id=team.organization_id,
                permission="team.update",
            )
            if not mt_store.delete_team_member(team_id, user_id):
                raise NotFoundError("team member not found")
            return {"ok": True, "removed": True, "teamId": team_id, "userId": user_id}

    def roles(self) -> dict[str, Any]:
        return {
            "ok": True,
            "roles": list(TEAM_ROLES),
            "permissions": {k: sorted(v) for k, v in TEAM_ROLE_PERMISSIONS.items()},
        }

    def permissions(self, team_role: str) -> dict[str, Any]:
        role = team_role.strip().lower()
        if role not in TEAM_ROLE_PERMISSIONS:
            raise ValidationError(f"unknown team role: {team_role}")
        return {
            "ok": True,
            "teamRole": role,
            "permissions": sorted(TEAM_ROLE_PERMISSIONS[role]),
        }


class MemberEngine:
    def invite(self, payload: dict[str, Any], *, actor_id: str | None = None) -> dict[str, Any]:
        return InvitationManager().create(payload, actor_id=actor_id)

    def remove(self, member_id: str, *, actor_id: str) -> dict[str, Any]:
        with om_store.timed_op():
            repo = get_repository()
            member = repo.get_member(member_id)
            if member is None:
                raise NotFoundError("member not found")
            enforce(
                actor_id=actor_id,
                organization_id=member.organization_id,
                permission="member.remove",
            )
            if member.role_key == "owner":
                raise ForbiddenError("cannot remove organization owner")
            mt_store.delete_member(member_id)
            om_store.add_activity(
                ActivityLog(
                    id=new_id("act_"),
                    organization_id=member.organization_id,
                    actor_id=actor_id,
                    action="member.removed",
                    detail=member.user_id,
                )
            )
            return {"ok": True, "removed": True, "memberId": member_id}

    def suspend(self, member_id: str, *, actor_id: str) -> dict[str, Any]:
        return self._set_status(member_id, "suspended", actor_id=actor_id)

    def reactivate(self, member_id: str, *, actor_id: str) -> dict[str, Any]:
        return self._set_status(member_id, "active", actor_id=actor_id)

    def change_role(self, member_id: str, role: str, *, actor_id: str) -> dict[str, Any]:
        with om_store.timed_op():
            repo = get_repository()
            member = repo.get_member(member_id)
            if member is None:
                raise NotFoundError("member not found")
            enforce(
                actor_id=actor_id,
                organization_id=member.organization_id,
                permission="role.assign",
            )
            role_key = validate_role(role)
            if member.role_key == "owner" and role_key != "owner":
                raise ForbiddenError("cannot demote owner; transfer ownership first")
            updated = get_multi_tenant_service().update_member_role(member_id, role_key)
            om_store.add_activity(
                ActivityLog(
                    id=new_id("act_"),
                    organization_id=member.organization_id,
                    actor_id=actor_id,
                    action="member.role_changed",
                    detail=f"{member.user_id}:{role_key}",
                )
            )
            return updated

    def _set_status(self, member_id: str, status: str, *, actor_id: str) -> dict[str, Any]:
        with om_store.timed_op():
            repo = get_repository()
            member = repo.get_member(member_id)
            if member is None:
                raise NotFoundError("member not found")
            enforce(
                actor_id=actor_id,
                organization_id=member.organization_id,
                permission="member.update",
            )
            if member.role_key == "owner" and status != "active":
                raise ForbiddenError("cannot suspend organization owner")
            member.status = status
            member.updated_at = _now()
            mt_store.save_member(member)
            om_store.add_activity(
                ActivityLog(
                    id=new_id("act_"),
                    organization_id=member.organization_id,
                    actor_id=actor_id,
                    action=f"member.{status}",
                    detail=member.user_id,
                )
            )
            return {"ok": True, "member": member.to_dict()}


class InvitationManager:
    def create(self, payload: dict[str, Any], *, actor_id: str | None = None) -> dict[str, Any]:
        with om_store.timed_op():
            data = validate_create_invite(payload)
            actor = actor_id or data["invited_by_id"]
            enforce(
                actor_id=actor,
                organization_id=data["organization_id"],
                permission="member.invite",
                workspace_id=data.get("workspace_id"),
            )
            settings = SettingsManager().get_org_settings(data["organization_id"])
            if settings and not settings.get("allowInvites", True):
                raise ForbiddenError("invitations are disabled for this organization")
            result = get_multi_tenant_service().create_invite(payload)
            om_store.add_activity(
                ActivityLog(
                    id=new_id("act_"),
                    organization_id=data["organization_id"],
                    workspace_id=data.get("workspace_id"),
                    actor_id=actor,
                    action="invitation.created",
                    detail=data["email"],
                )
            )
            return result

    def accept(self, token: str, user_id: str) -> dict[str, Any]:
        with om_store.timed_op():
            result = get_multi_tenant_service().accept_invite(token, user_id)
            om_store.add_activity(
                ActivityLog(
                    id=new_id("act_"),
                    organization_id=result["invite"]["organizationId"],
                    workspace_id=result["invite"].get("workspaceId"),
                    actor_id=user_id,
                    action="invitation.accepted",
                )
            )
            audit(
                "invite_accepted",
                actor_id=user_id,
                organization_id=result["invite"]["organizationId"],
                success=True,
            )
            return result

    def reject(self, token: str, *, actor_id: str | None = None) -> dict[str, Any]:
        with om_store.timed_op():
            invite = get_repository().get_invite_by_token(token)
            if invite is None:
                raise NotFoundError("invite not found")
            if invite.status != "pending":
                raise ValidationError(f"invite is {invite.status}")
            invite.status = "rejected"
            invite.updated_at = _now()
            mt_store.save_invite(invite)
            om_store.add_activity(
                ActivityLog(
                    id=new_id("act_"),
                    organization_id=invite.organization_id,
                    actor_id=actor_id or "system",
                    action="invitation.rejected",
                    detail=invite.email,
                )
            )
            return {"ok": True, "invite": invite.to_dict()}


class SettingsManager:
    def ensure_org_settings(self, organization_id: str) -> dict[str, Any]:
        existing = om_store.get_org_settings(organization_id)
        if existing:
            return existing.to_dict()
        settings = OrganizationSettings(
            id=new_id("oset_"), organization_id=organization_id
        )
        return om_store.save_org_settings(settings).to_dict()

    def get_org_settings(self, organization_id: str) -> dict[str, Any]:
        return self.ensure_org_settings(organization_id)

    def update_org_settings(
        self, organization_id: str, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with om_store.timed_op():
            enforce(actor_id=actor_id, organization_id=organization_id, permission="org.update")
            current = om_store.get_org_settings(organization_id)
            if current is None:
                current = OrganizationSettings(
                    id=new_id("oset_"), organization_id=organization_id
                )
            if payload.get("timezone"):
                current.timezone = str(payload["timezone"])
            if payload.get("locale"):
                current.locale = str(payload["locale"])
            if "allowInvites" in payload or "allow_invites" in payload:
                current.allow_invites = bool(
                    payload.get("allowInvites", payload.get("allow_invites"))
                )
            if payload.get("defaultRole") or payload.get("default_role"):
                current.default_role = validate_role_key(
                    payload.get("defaultRole") or payload.get("default_role")
                )
            if payload.get("settings") is not None:
                if not isinstance(payload["settings"], dict):
                    raise ValidationError("settings must be an object")
                current.settings = dict(payload["settings"])
            current.updated_at = _now()
            return {"ok": True, "settings": om_store.save_org_settings(current).to_dict()}

    def ensure_ws_settings(self, workspace_id: str) -> dict[str, Any]:
        existing = om_store.get_ws_settings(workspace_id)
        if existing:
            return existing.to_dict()
        settings = WorkspaceSettings(id=new_id("wset_"), workspace_id=workspace_id)
        return om_store.save_ws_settings(settings).to_dict()

    def update_ws_settings(
        self, workspace_id: str, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        repo = get_repository()
        ws = repo.get_workspace(workspace_id)
        if ws is None:
            raise NotFoundError("workspace not found")
        enforce(
            actor_id=actor_id,
            organization_id=ws.organization_id,
            workspace_id=workspace_id,
            permission="workspace.update",
        )
        current = om_store.get_ws_settings(workspace_id)
        if current is None:
            current = WorkspaceSettings(id=new_id("wset_"), workspace_id=workspace_id)
        if payload.get("visibility"):
            current.visibility = str(payload["visibility"])
        if "defaultModel" in payload or "default_model" in payload:
            current.default_model = payload.get("defaultModel") or payload.get("default_model")
        if payload.get("settings") is not None:
            if not isinstance(payload["settings"], dict):
                raise ValidationError("settings must be an object")
            current.settings = dict(payload["settings"])
        current.updated_at = _now()
        return {"ok": True, "settings": om_store.save_ws_settings(current).to_dict()}


class OrgManagementService:
    def __init__(self) -> None:
        self.organizations = OrganizationEngine()
        self.workspaces = WorkspaceEngine()
        self.teams = TeamEngine()
        self.members = MemberEngine()
        self.invitations = InvitationManager()
        self.settings = SettingsManager()

    def status(self) -> dict[str, Any]:
        mt_stats = get_repository().stats()
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "modules": [
                "organization_engine",
                "workspace_engine",
                "team_engine",
                "member_engine",
                "invitation_manager",
                "settings_manager",
            ],
            "stats": {
                **mt_stats,
                **om_store.metrics(),
                "invitationStatus": {
                    "pending": sum(
                        1
                        for o in mt_store.list_organizations()
                        for i in mt_store.list_invites(o.id, status="pending")
                    ),
                },
            },
            "engines": {
                "organization": "ready",
                "workspace": "ready",
                "team": "ready",
                "member": "ready",
                "invitation": "ready",
                "settings": "ready",
            },
        }

    def observability(self) -> dict[str, Any]:
        status = self.status()
        return {
            "ok": True,
            "organizationCount": status["stats"].get("organizations", 0),
            "workspaceCount": status["stats"].get("workspaces", 0),
            "teamCount": status["stats"].get("teams", 0),
            "memberCount": status["stats"].get("members", 0),
            "invitationStatus": status["stats"].get("invitationStatus", {}),
            "apiPerformance": {
                "calls": status["stats"].get("apiCalls", 0),
                "avgLatencyMs": status["stats"].get("avgLatencyMs", 0),
                "p95LatencyMs": status["stats"].get("p95LatencyMs", 0),
            },
            "errors": status["stats"].get("errors", 0),
            "activityLogs": status["stats"].get("activityLogs", 0),
        }


_service: OrgManagementService | None = None


def get_org_management_service() -> OrgManagementService:
    global _service
    get_repository().ensure_system_rbac()
    if _service is None:
        _service = OrgManagementService()
    return _service


def reset_engine() -> None:
    global _service
    om_store.reset_store()
    from app.services.multi_tenant.engine import reset_engine as reset_mt
    from app.services.enterprise_auth.engine import reset_engine as reset_ea

    reset_mt()
    reset_ea()
    _service = None


get_engine = get_org_management_service

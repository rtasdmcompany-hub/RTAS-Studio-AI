"""Enterprise Notifications, Comments & Activity Engine — Phase 7 Sprint 6."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.services.enterprise_comms import store
from app.services.enterprise_comms.catalog import (
    ACTIVITY_CATEGORIES,
    ANNOUNCEMENT_SCOPES,
    MENTION_SUBJECT_TYPES,
    NOTIFICATION_TYPES,
    RESOURCE_TYPES,
    normalize_notification_type,
    normalize_resource_type,
)
from app.services.enterprise_comms.models import (
    ActivityEvent,
    Announcement,
    Comment,
    CommentReply,
    Mention,
    Notification,
    NotificationPreference,
    UserActivityLog,
    new_id,
)
from app.services.enterprise_comms.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    SPRINT,
)
from app.services.enterprise_auth.audit import log_auth_event
from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError
from app.services.enterprise_auth.middleware import require_access
from app.services.multi_tenant.repository import get_repository
from app.services.multi_tenant.validation import ValidationError, require_non_empty

_MENTION_RE = re.compile(r"@(user|team|organization):([A-Za-z0-9_\-]+)|@([A-Za-z0-9_\-]+)")


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


class NotificationPreferenceManager:
    def get(self, *, user_id: str, organization_id: str | None = None) -> dict[str, Any]:
        pref = store.get_preference(user_id, organization_id)
        if pref is None:
            pref = NotificationPreference(
                id=new_id("npref_"),
                user_id=user_id,
                organization_id=organization_id,
            )
            store.save_preference(pref)
        return {"ok": True, "preference": pref.to_dict()}

    def update(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        org_id = payload.get("organizationId") or payload.get("organization_id")
        if org_id:
            require_access(user_id=actor_id, organization_id=str(org_id), permission="content.read")
        pref = store.get_preference(actor_id, str(org_id) if org_id else None)
        if pref is None:
            pref = NotificationPreference(
                id=new_id("npref_"),
                user_id=actor_id,
                organization_id=str(org_id) if org_id else None,
            )
        if "channelEmail" in payload or "channel_email" in payload:
            pref.channel_email = bool(payload.get("channelEmail", payload.get("channel_email")))
        if "channelInApp" in payload or "channel_in_app" in payload:
            pref.channel_in_app = bool(payload.get("channelInApp", payload.get("channel_in_app")))
        if "digestsEnabled" in payload or "digests_enabled" in payload:
            pref.digests_enabled = bool(payload.get("digestsEnabled", payload.get("digests_enabled")))
        muted = payload.get("mutedTypes") or payload.get("muted_types")
        if muted is not None:
            if not isinstance(muted, list):
                raise ValidationError("mutedTypes must be a list")
            pref.muted_types = [str(t).lower() for t in muted]
        pref.updated_at = _now()
        store.save_preference(pref)
        _audit("notification.preferences_updated", actor_id)
        return {"ok": True, "preference": pref.to_dict()}

    def allows(self, *, user_id: str, organization_id: str, ntype: str) -> bool:
        pref = store.get_preference(user_id, organization_id) or store.get_preference(user_id, None)
        if pref is None:
            return True
        if not pref.channel_in_app:
            return False
        return ntype not in pref.muted_types


class NotificationEngine:
    def __init__(self) -> None:
        self.prefs = NotificationPreferenceManager()

    def send(self, payload: dict[str, Any], *, actor_id: str | None = None) -> dict[str, Any]:
        with store.timed_op():
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            recipient_id = require_non_empty(
                payload.get("recipientId") or payload.get("recipient_id"),
                "recipientId",
            )
            try:
                ntype = normalize_notification_type(str(payload.get("type") or "system_alert"))
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc
            if not self.prefs.allows(user_id=recipient_id, organization_id=org_id, ntype=ntype):
                return {"ok": True, "skipped": True, "reason": "muted_or_disabled"}
            title = require_non_empty(payload.get("title"), "title", max_len=200)
            note = Notification(
                id=new_id("notif_"),
                organization_id=org_id,
                workspace_id=payload.get("workspaceId") or payload.get("workspace_id"),
                recipient_id=recipient_id,
                type=ntype,
                title=title,
                body=payload.get("body"),
                resource_type=payload.get("resourceType") or payload.get("resource_type"),
                resource_id=payload.get("resourceId") or payload.get("resource_id"),
                actor_id=actor_id or payload.get("actorId"),
                metadata=dict(payload.get("metadata") or {}),
            )
            store.save_notification(note)
            store.touch_user(recipient_id)
            if actor_id:
                _audit("notification.sent", actor_id, note.title, type=ntype, recipientId=recipient_id)
            return {"ok": True, "notification": note.to_dict()}

    def list(
        self,
        *,
        actor_id: str,
        organization_id: str | None = None,
        unread_only: bool = False,
        limit: int = 50,
    ) -> dict[str, Any]:
        with store.timed_op():
            if organization_id:
                require_access(
                    user_id=actor_id, organization_id=organization_id, permission="content.read"
                )
            store.touch_user(actor_id)
            items = store.list_notifications(
                recipient_id=actor_id,
                organization_id=organization_id,
                unread_only=unread_only,
                limit=limit,
            )
            # privacy: only recipient's inbox
            return {
                "ok": True,
                "count": len(items),
                "unreadCount": sum(1 for n in items if not n.is_read),
                "notifications": [n.to_dict() for n in items],
            }

    def mark_read(self, ids: list[str], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            if not ids:
                raise ValidationError("ids required")
            # enforce ownership — only mark own notifications
            owned = []
            for nid in ids:
                n = store.get_notification(nid)
                if n is None:
                    continue
                if n.recipient_id != actor_id:
                    raise ForbiddenError("notification privacy violation")
                owned.append(nid)
            count = store.mark_read(owned, recipient_id=actor_id)
            _audit("notification.read", actor_id, detail=str(count))
            return {"ok": True, "marked": count}

    def mark_all_read(self, *, actor_id: str, organization_id: str | None = None) -> dict[str, Any]:
        with store.timed_op():
            if organization_id:
                require_access(
                    user_id=actor_id, organization_id=organization_id, permission="content.read"
                )
            count = store.mark_all_read(recipient_id=actor_id, organization_id=organization_id)
            _audit("notification.read_all", actor_id, detail=str(count))
            return {"ok": True, "marked": count}


class MentionEngine:
    def __init__(self) -> None:
        self.notifications = NotificationEngine()

    def parse(self, body: str) -> list[tuple[str, str]]:
        found: list[tuple[str, str]] = []
        for m in _MENTION_RE.finditer(body or ""):
            if m.group(1) and m.group(2):
                found.append((m.group(1).lower(), m.group(2)))
            elif m.group(3):
                found.append(("user", m.group(3)))
        # dedupe
        seen: set[tuple[str, str]] = set()
        out: list[tuple[str, str]] = []
        for item in found:
            if item not in seen and item[0] in MENTION_SUBJECT_TYPES:
                seen.add(item)
                out.append(item)
        return out

    def resolve_targets(
        self, organization_id: str, subject_type: str, subject_id: str
    ) -> list[str]:
        repo = get_repository()
        if subject_type == "user":
            member = repo.get_member_by_org_user(organization_id, subject_id)
            return [subject_id] if member else []
        if subject_type == "organization":
            members = repo.list_members(organization_id)
            if members:
                return [
                    m.user_id
                    for m in members
                    if getattr(m, "status", "active") == "active"
                ]
            org = repo.get_organization(organization_id)
            return [org.owner_id] if org else []
        if subject_type == "team":
            team = repo.get_team(subject_id)
            if team is None or team.organization_id != organization_id:
                return []
            return [tm.user_id for tm in repo.list_team_members(subject_id)]
        return []

    def process(
        self,
        *,
        body: str,
        organization_id: str,
        actor_id: str,
        comment_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> dict[str, Any]:
        parsed = self.parse(body)
        created: list[dict[str, Any]] = []
        notified: set[str] = set()
        for subject_type, subject_id in parsed:
            targets = self.resolve_targets(organization_id, subject_type, subject_id)
            for uid in targets:
                if uid == actor_id:
                    continue
                mention = Mention(
                    id=new_id("ment_"),
                    comment_id=comment_id,
                    organization_id=organization_id,
                    actor_id=actor_id,
                    subject_type=subject_type,
                    subject_id=subject_id,
                    target_user_id=uid,
                    resource_type=resource_type,
                    resource_id=resource_id,
                )
                store.save_mention(mention)
                created.append(mention.to_dict())
                if uid not in notified:
                    notified.add(uid)
                    self.notifications.send(
                        {
                            "organizationId": organization_id,
                            "recipientId": uid,
                            "type": "mention_received",
                            "title": f"You were mentioned by {actor_id}",
                            "body": body[:240],
                            "resourceType": resource_type,
                            "resourceId": resource_id,
                            "actorId": actor_id,
                        },
                        actor_id=actor_id,
                    )
        return {"ok": True, "count": len(created), "mentions": created, "notified": list(notified)}


class ActivityFeedEngine:
    def emit(self, payload: dict[str, Any], *, actor_id: str | None = None) -> dict[str, Any]:
        with store.timed_op():
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            category = str(payload.get("category") or "system").lower()
            if category not in ACTIVITY_CATEGORIES:
                raise ValidationError(f"unsupported activity category: {category}")
            action = require_non_empty(payload.get("action"), "action", max_len=80)
            summary = require_non_empty(payload.get("summary"), "summary", max_len=400)
            event = ActivityEvent(
                id=new_id("aevt_"),
                organization_id=org_id,
                workspace_id=payload.get("workspaceId") or payload.get("workspace_id"),
                actor_id=actor_id or payload.get("actorId"),
                category=category,
                action=action,
                summary=summary,
                resource_type=payload.get("resourceType") or payload.get("resource_type"),
                resource_id=payload.get("resourceId") or payload.get("resource_id"),
                metadata=dict(payload.get("metadata") or {}),
            )
            store.save_activity(event)
            if actor_id:
                store.touch_user(actor_id)
                store.save_user_log(
                    UserActivityLog(
                        id=new_id("ulog_"),
                        user_id=actor_id,
                        organization_id=org_id,
                        workspace_id=event.workspace_id,
                        action=action,
                        detail=summary,
                        metadata={"category": category},
                    )
                )
            return {"ok": True, "event": event.to_dict()}

    def list(
        self,
        *,
        actor_id: str,
        organization_id: str,
        workspace_id: str | None = None,
        category: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        with store.timed_op():
            require_access(
                user_id=actor_id,
                organization_id=organization_id,
                workspace_id=workspace_id,
                permission="content.read",
            )
            if workspace_id:
                ws = get_repository().get_workspace(workspace_id)
                if ws is None or ws.organization_id != organization_id:
                    raise ForbiddenError("workspace isolation violation")
            items = store.list_activity(
                organization_id=organization_id,
                workspace_id=workspace_id,
                category=category,
                limit=limit,
            )
            return {"ok": True, "count": len(items), "activity": [e.to_dict() for e in items]}

    def log_login(self, *, actor_id: str, organization_id: str | None = None) -> dict[str, Any]:
        store.save_user_log(
            UserActivityLog(
                id=new_id("ulog_"),
                user_id=actor_id,
                organization_id=organization_id,
                action="user.login",
                detail="User login",
            )
        )
        store.touch_user(actor_id)
        if organization_id:
            return self.emit(
                {
                    "organizationId": organization_id,
                    "category": "user_login",
                    "action": "user.login",
                    "summary": f"User {actor_id} logged in",
                },
                actor_id=actor_id,
            )
        return {"ok": True, "logged": True}


class CommentEngine:
    def __init__(self) -> None:
        self.mentions = MentionEngine()
        self.activity = ActivityFeedEngine()
        self.notifications = NotificationEngine()

    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            require_access(user_id=actor_id, organization_id=org_id, permission="content.write")
            workspace_id = payload.get("workspaceId") or payload.get("workspace_id")
            if workspace_id:
                ws = get_repository().get_workspace(str(workspace_id))
                if ws is None or ws.organization_id != org_id:
                    raise ForbiddenError("workspace isolation violation")
            try:
                resource_type = normalize_resource_type(
                    str(payload.get("resourceType") or payload.get("resource_type") or "project")
                )
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc
            resource_id = require_non_empty(
                payload.get("resourceId") or payload.get("resource_id"), "resourceId"
            )
            body = require_non_empty(payload.get("body"), "body", max_len=5000)
            parent_id = payload.get("parentId") or payload.get("parent_id")
            if parent_id:
                parent = store.get_comment(str(parent_id))
                if parent is None or parent.deleted_at is not None:
                    raise NotFoundError("parent comment not found")
                if parent.organization_id != org_id:
                    raise ForbiddenError("organization isolation violation")
                reply = CommentReply(
                    id=new_id("creply_"),
                    comment_id=parent.id,
                    author_id=actor_id,
                    body=body,
                )
                store.save_reply(reply)
                mention_result = self.mentions.process(
                    body=body,
                    organization_id=org_id,
                    actor_id=actor_id,
                    comment_id=parent.id,
                    resource_type=parent.resource_type,
                    resource_id=parent.resource_id,
                )
                self.activity.emit(
                    {
                        "organizationId": org_id,
                        "workspaceId": parent.workspace_id,
                        "category": "comment",
                        "action": "comment.replied",
                        "summary": f"Reply on {parent.resource_type}",
                        "resourceType": parent.resource_type,
                        "resourceId": parent.resource_id,
                    },
                    actor_id=actor_id,
                )
                _audit("comment.replied", actor_id, parent.id)
                return {
                    "ok": True,
                    "reply": reply.to_dict(),
                    "mentions": mention_result["mentions"],
                }

            comment = Comment(
                id=new_id("cmt_"),
                organization_id=org_id,
                workspace_id=str(workspace_id) if workspace_id else None,
                author_id=actor_id,
                resource_type=resource_type,
                resource_id=resource_id,
                body=body,
            )
            store.save_comment(comment)
            mention_result = self.mentions.process(
                body=body,
                organization_id=org_id,
                actor_id=actor_id,
                comment_id=comment.id,
                resource_type=resource_type,
                resource_id=resource_id,
            )
            # notify resource watchers via comment_added if recipient provided
            notify_user = payload.get("notifyUserId") or payload.get("notify_user_id")
            if notify_user and notify_user != actor_id:
                self.notifications.send(
                    {
                        "organizationId": org_id,
                        "workspaceId": workspace_id,
                        "recipientId": notify_user,
                        "type": "comment_added",
                        "title": "New comment",
                        "body": body[:240],
                        "resourceType": resource_type,
                        "resourceId": resource_id,
                        "actorId": actor_id,
                    },
                    actor_id=actor_id,
                )
            self.activity.emit(
                {
                    "organizationId": org_id,
                    "workspaceId": workspace_id,
                    "category": "comment",
                    "action": "comment.added",
                    "summary": f"Comment on {resource_type}",
                    "resourceType": resource_type,
                    "resourceId": resource_id,
                },
                actor_id=actor_id,
            )
            _audit("comment.created", actor_id, comment.id)
            return {
                "ok": True,
                "comment": comment.to_dict(),
                "mentions": mention_result["mentions"],
            }

    def update(self, comment_id: str, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            comment = store.get_comment(comment_id)
            if comment is None or comment.deleted_at is not None:
                raise NotFoundError("comment not found")
            require_access(
                user_id=actor_id,
                organization_id=comment.organization_id,
                permission="content.write",
            )
            is_author = comment.author_id == actor_id
            if payload.get("body") is not None:
                if not is_author:
                    raise ForbiddenError("comment edit requires author")
                comment.body = require_non_empty(payload.get("body"), "body", max_len=5000)
            if "isPinned" in payload or "is_pinned" in payload:
                # pin requires write access (already checked)
                comment.is_pinned = bool(payload.get("isPinned", payload.get("is_pinned")))
            if "isResolved" in payload or "is_resolved" in payload:
                comment.is_resolved = bool(payload.get("isResolved", payload.get("is_resolved")))
            emoji = payload.get("reaction") or payload.get("emoji")
            if emoji:
                key = str(emoji)[:16]
                users = list(comment.reactions.get(key) or [])
                if actor_id in users:
                    users = [u for u in users if u != actor_id]
                else:
                    users.append(actor_id)
                comment.reactions[key] = users
            comment.updated_at = _now()
            store.save_comment(comment)
            _audit("comment.updated", actor_id, comment_id)
            return {"ok": True, "comment": comment.to_dict()}

    def delete(self, comment_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            comment = store.get_comment(comment_id)
            if comment is None or comment.deleted_at is not None:
                raise NotFoundError("comment not found")
            require_access(
                user_id=actor_id,
                organization_id=comment.organization_id,
                permission="content.write",
            )
            member = get_repository().get_member_by_org_user(comment.organization_id, actor_id)
            role_key = getattr(member, "role_key", None) if member else None
            if comment.author_id != actor_id and role_key not in {"owner", "admin"}:
                raise ForbiddenError("comment delete requires author or admin")
            comment.deleted_at = _now()
            comment.updated_at = _now()
            store.save_comment(comment)
            _audit("comment.deleted", actor_id, comment_id)
            return {"ok": True, "deleted": True, "comment": comment.to_dict()}

    def list_for_resource(
        self,
        resource_id: str,
        *,
        actor_id: str,
        organization_id: str | None = None,
        resource_type: str | None = None,
    ) -> dict[str, Any]:
        with store.timed_op():
            items = store.list_comments(
                resource_id=resource_id,
                resource_type=resource_type,
                organization_id=organization_id,
            )
            if not items and organization_id:
                require_access(
                    user_id=actor_id, organization_id=organization_id, permission="content.read"
                )
            elif items:
                org_id = items[0].organization_id
                require_access(user_id=actor_id, organization_id=org_id, permission="content.read")
                if organization_id and organization_id != org_id:
                    raise ForbiddenError("organization isolation violation")
            result = []
            for c in items:
                data = c.to_dict()
                data["replies"] = [r.to_dict() for r in store.list_replies(c.id)]
                result.append(data)
            return {"ok": True, "count": len(result), "comments": result}


class AnnouncementEngine:
    def __init__(self) -> None:
        self.notifications = NotificationEngine()
        self.activity = ActivityFeedEngine()

    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            require_access(user_id=actor_id, organization_id=org_id, permission="org.update")
            scope = str(payload.get("scope") or "organization").lower()
            if scope not in ANNOUNCEMENT_SCOPES:
                raise ValidationError("scope must be organization|workspace|team")
            ann = Announcement(
                id=new_id("ann_"),
                organization_id=org_id,
                workspace_id=payload.get("workspaceId") or payload.get("workspace_id"),
                author_id=actor_id,
                title=require_non_empty(payload.get("title"), "title", max_len=200),
                body=require_non_empty(payload.get("body"), "body", max_len=5000),
                scope=scope,
                is_pinned=bool(payload.get("isPinned") or payload.get("is_pinned")),
            )
            store.save_announcement(ann)
            # notify org owner at minimum
            org = get_repository().get_organization(org_id)
            recipients = {actor_id}
            if org:
                recipients.add(org.owner_id)
            for uid in recipients:
                if uid == actor_id:
                    continue
                self.notifications.send(
                    {
                        "organizationId": org_id,
                        "workspaceId": ann.workspace_id,
                        "recipientId": uid,
                        "type": "announcement",
                        "title": ann.title,
                        "body": ann.body[:240],
                        "resourceType": "organization",
                        "resourceId": org_id,
                        "actorId": actor_id,
                    },
                    actor_id=actor_id,
                )
            self.activity.emit(
                {
                    "organizationId": org_id,
                    "workspaceId": ann.workspace_id,
                    "category": "announcement",
                    "action": "announcement.published",
                    "summary": ann.title,
                    "resourceType": "organization",
                    "resourceId": org_id,
                },
                actor_id=actor_id,
            )
            _audit("announcement.created", actor_id, ann.id)
            return {"ok": True, "announcement": ann.to_dict()}

    def list(self, *, actor_id: str, organization_id: str, workspace_id: str | None = None) -> dict[str, Any]:
        require_access(user_id=actor_id, organization_id=organization_id, permission="content.read")
        items = store.list_announcements(organization_id=organization_id, workspace_id=workspace_id)
        return {"ok": True, "count": len(items), "announcements": [a.to_dict() for a in items]}


class EnterpriseCommsService:
    def __init__(self) -> None:
        self.notifications = NotificationEngine()
        self.comments = CommentEngine()
        self.activity = ActivityFeedEngine()
        self.mentions = MentionEngine()
        self.announcements = AnnouncementEngine()
        self.preferences = NotificationPreferenceManager()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "modules": [
                "notification_engine",
                "comment_engine",
                "activity_feed_engine",
                "mention_engine",
                "announcement_engine",
                "notification_preference_manager",
            ],
            "notificationTypes": list(NOTIFICATION_TYPES),
            "resourceTypes": list(RESOURCE_TYPES),
            "activityCategories": list(ACTIVITY_CATEGORIES),
            "stats": store.metrics(),
            "engines": {
                "notifications": "ready",
                "comments": "ready",
                "activity": "ready",
                "mentions": "ready",
                "announcements": "ready",
                "preferences": "ready",
            },
        }

    def observability(self) -> dict[str, Any]:
        m = store.metrics()
        return {
            "ok": True,
            "notificationsSent": m["notificationsSent"],
            "notificationsRead": m["notificationsRead"],
            "activeUsers": m["activeUsers"],
            "commentCount": m["commentCount"],
            "mentionCount": m["mentionCount"],
            "activityEvents": m["activityEvents"],
            "apiPerformance": {
                "calls": m["apiCalls"],
                "avgLatencyMs": m["avgLatencyMs"],
            },
            "errors": m["errors"],
        }


_service: EnterpriseCommsService | None = None


def get_enterprise_comms_service() -> EnterpriseCommsService:
    global _service
    if _service is None:
        _service = EnterpriseCommsService()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    from app.services.multi_tenant.engine import reset_engine as reset_mt
    from app.services.enterprise_auth.engine import reset_engine as reset_ea

    reset_mt()
    reset_ea()
    _service = None


get_engine = get_enterprise_comms_service

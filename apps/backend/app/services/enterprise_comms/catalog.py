"""Notification types, resource types, and activity categories."""

from __future__ import annotations

from typing import Final

NOTIFICATION_TYPES: Final[tuple[str, ...]] = (
    "project_created",
    "project_updated",
    "project_deleted",
    "member_invited",
    "member_joined",
    "comment_added",
    "mention_received",
    "ai_job_started",
    "ai_job_completed",
    "export_ready",
    "download_available",
    "billing_event",
    "system_alert",
    "announcement",
)

RESOURCE_TYPES: Final[tuple[str, ...]] = (
    "project",
    "asset",
    "ai_job",
    "organization",
    "workspace",
    "team",
    "export",
    "download",
)

ACTIVITY_CATEGORIES: Final[tuple[str, ...]] = (
    "user_login",
    "project",
    "asset",
    "ai_generation",
    "team",
    "organization",
    "workspace",
    "export",
    "download",
    "comment",
    "announcement",
    "system",
)

MENTION_SUBJECT_TYPES: Final[tuple[str, ...]] = ("user", "team", "organization")

ANNOUNCEMENT_SCOPES: Final[tuple[str, ...]] = ("organization", "workspace", "team")


def normalize_notification_type(value: str) -> str:
    key = value.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "project.created": "project_created",
        "project.updated": "project_updated",
        "project.deleted": "project_deleted",
        "member.invited": "member_invited",
        "member.joined": "member_joined",
        "comment.added": "comment_added",
        "mention.received": "mention_received",
        "ai.job.started": "ai_job_started",
        "ai.job.completed": "ai_job_completed",
        "export.ready": "export_ready",
        "download.available": "download_available",
        "billing.events": "billing_event",
        "billing_events": "billing_event",
        "system.alerts": "system_alert",
        "system_alerts": "system_alert",
    }
    key = aliases.get(key, key)
    if key not in NOTIFICATION_TYPES:
        raise ValueError(f"unsupported notification type: {value}")
    return key


def normalize_resource_type(value: str) -> str:
    key = value.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {"ai-job": "ai_job", "aijob": "ai_job", "jobs": "ai_job"}
    key = aliases.get(key, key)
    if key not in RESOURCE_TYPES:
        raise ValueError(f"unsupported resource type: {value}")
    return key

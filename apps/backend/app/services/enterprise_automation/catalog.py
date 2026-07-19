"""Automation modes, event types, triggers, and integration providers."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from typing import Final

AUTOMATION_MODES: Final[tuple[str, ...]] = (
    "event",
    "scheduled",
    "manual",
    "conditional",
    "multi_step",
    "ai_workflow",
    "background",
    "queue",
)

AUTOMATION_STATUSES: Final[tuple[str, ...]] = (
    "active",
    "paused",
    "disabled",
    "archived",
)

EVENT_CATEGORIES: Final[tuple[str, ...]] = (
    "user",
    "organization",
    "workspace",
    "project",
    "ai_generation",
    "asset",
    "billing",
    "marketplace",
    "notification",
    "webhook",
)

EVENT_TYPES: Final[tuple[str, ...]] = (
    "user.registered",
    "project.created",
    "asset.uploaded",
    "ai.job.completed",
    "payment.completed",
    "subscription.renewed",
    "marketplace.purchase",
    "webhook.received",
    "custom.event",
    "organization.updated",
    "workspace.created",
    "notification.sent",
)

INTEGRATION_PROVIDERS: Final[tuple[str, ...]] = (
    "google_drive",
    "dropbox",
    "onedrive",
    "github",
    "slack",
    "discord",
    "zapier",
    "make",
    "microsoft_teams",
    "webhook",
    "custom",
)

EXECUTION_STATUSES: Final[tuple[str, ...]] = (
    "queued",
    "running",
    "completed",
    "failed",
    "skipped",
    "cancelled",
)

SCHEDULE_KINDS: Final[tuple[str, ...]] = (
    "once",
    "recurring",
    "daily",
    "weekly",
    "monthly",
)

WEBHOOK_SIGNING_SECRET: Final[str] = "rtas-automation-webhook-v1"

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    slug = _SLUG_RE.sub("-", (value or "").lower()).strip("-")
    return slug or "automation"


def category_for_event(event_type: str) -> str:
    prefix = (event_type or "").split(".", 1)[0]
    mapping = {
        "user": "user",
        "project": "project",
        "asset": "asset",
        "ai": "ai_generation",
        "payment": "billing",
        "subscription": "billing",
        "marketplace": "marketplace",
        "webhook": "webhook",
        "organization": "organization",
        "workspace": "workspace",
        "notification": "notification",
        "custom": "webhook",
    }
    return mapping.get(prefix, "webhook")


def sign_webhook_payload(payload: str, secret: str = "") -> str:
    key = (secret or WEBHOOK_SIGNING_SECRET).encode("utf-8")
    return hmac.new(key, payload.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_webhook_signature(payload: str, signature: str, secret: str = "") -> bool:
    if not signature:
        return False
    expected = sign_webhook_payload(payload, secret)
    return hmac.compare_digest(expected, signature)


def generate_credentials_ref(provider: str) -> str:
    return f"vault://automation/{provider}/{secrets.token_hex(8)}"

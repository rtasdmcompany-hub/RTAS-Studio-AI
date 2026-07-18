"""Workflow statuses, change types, and review scopes."""

from __future__ import annotations

from typing import Final

VERSION_STATUSES: Final[tuple[str, ...]] = (
    "draft",
    "pending_review",
    "under_review",
    "approved",
    "rejected",
    "needs_changes",
    "published",
    "archived",
)

APPROVAL_STATUSES: Final[tuple[str, ...]] = VERSION_STATUSES

REVIEW_TYPES: Final[tuple[str, ...]] = (
    "internal",
    "team",
    "organization",
)

CHANGE_TYPES: Final[tuple[str, ...]] = (
    "prompt",
    "asset",
    "project",
    "ai_output",
    "member",
    "workflow",
    "timeline",
    "export",
    "version",
    "rollback",
    "review",
)

# Allowed transitions for approval workflow
TRANSITIONS: Final[dict[str, set[str]]] = {
    "draft": {"pending_review", "archived"},
    "pending_review": {"under_review", "draft", "rejected"},
    "under_review": {"approved", "rejected", "needs_changes"},
    "approved": {"published", "needs_changes", "archived"},
    "rejected": {"draft", "pending_review", "archived"},
    "needs_changes": {"draft", "pending_review", "archived"},
    "published": {"archived", "needs_changes"},
    "archived": {"draft"},
}


def normalize_status(value: str) -> str:
    key = value.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "pending": "pending_review",
        "in_review": "under_review",
        "needs_change": "needs_changes",
        "need_changes": "needs_changes",
    }
    key = aliases.get(key, key)
    if key not in VERSION_STATUSES:
        raise ValueError(f"unsupported status: {value}")
    return key


def normalize_change_type(value: str) -> str:
    key = value.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "prompts": "prompt",
        "assets": "asset",
        "projects": "project",
        "ai_outputs": "ai_output",
        "members": "member",
        "workflows": "workflow",
        "timelines": "timeline",
        "exports": "export",
    }
    key = aliases.get(key, key)
    if key not in CHANGE_TYPES:
        raise ValueError(f"unsupported change type: {value}")
    return key


def can_transition(from_status: str, to_status: str) -> bool:
    return to_status in TRANSITIONS.get(from_status, set())

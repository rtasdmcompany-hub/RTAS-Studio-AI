"""Input validation for multi-tenant operations."""

from __future__ import annotations

import re
from typing import Any

from app.services.multi_tenant.roles import SYSTEM_ROLE_KEYS

_SLUG_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(ValueError):
    """Raised when multi-tenant input fails validation."""


def require_non_empty(value: Any, field: str, *, max_len: int = 200) -> str:
    if value is None:
        raise ValidationError(f"{field} is required")
    text = str(value).strip()
    if not text:
        raise ValidationError(f"{field} is required")
    if len(text) > max_len:
        raise ValidationError(f"{field} must be at most {max_len} characters")
    return text


def normalize_slug(value: Any, field: str = "slug") -> str:
    text = require_non_empty(value, field, max_len=64).lower()
    text = re.sub(r"[^a-z0-9-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    if not text or not _SLUG_RE.match(text):
        raise ValidationError(
            f"{field} must be 2-64 chars, lowercase alphanumeric with hyphens"
        )
    return text


def slug_from_name(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not base:
        base = "org"
    if len(base) < 2:
        base = f"{base}x"
    return base[:64]


def validate_email(value: Any) -> str:
    email = require_non_empty(value, "email", max_len=320).lower()
    if not _EMAIL_RE.match(email):
        raise ValidationError("email is invalid")
    return email


def validate_role_key(value: Any) -> str:
    key = require_non_empty(value, "role", max_len=64).lower()
    if key not in SYSTEM_ROLE_KEYS:
        raise ValidationError(
            f"role must be one of: {', '.join(SYSTEM_ROLE_KEYS)}"
        )
    return key


def validate_plan(value: Any | None) -> str:
    if value is None or str(value).strip() == "":
        return "free"
    plan = str(value).strip().lower()
    allowed = {"free", "starter", "pro", "enterprise"}
    if plan not in allowed:
        raise ValidationError(f"plan must be one of: {', '.join(sorted(allowed))}")
    return plan


def validate_create_organization(payload: dict[str, Any]) -> dict[str, Any]:
    name = require_non_empty(payload.get("name"), "name", max_len=120)
    owner_id = require_non_empty(payload.get("ownerId") or payload.get("owner_id"), "ownerId")
    slug_raw = payload.get("slug")
    slug = normalize_slug(slug_raw) if slug_raw else normalize_slug(slug_from_name(name))
    plan = validate_plan(payload.get("plan"))
    metadata = payload.get("metadata") or {}
    if metadata is not None and not isinstance(metadata, dict):
        raise ValidationError("metadata must be an object")
    return {
        "name": name,
        "slug": slug,
        "owner_id": owner_id,
        "plan": plan,
        "metadata": dict(metadata or {}),
    }


def validate_create_workspace(payload: dict[str, Any]) -> dict[str, Any]:
    name = require_non_empty(payload.get("name"), "name", max_len=120)
    org_id = require_non_empty(
        payload.get("organizationId") or payload.get("organization_id"),
        "organizationId",
    )
    slug_raw = payload.get("slug")
    slug = normalize_slug(slug_raw) if slug_raw else normalize_slug(slug_from_name(name))
    metadata = payload.get("metadata") or {}
    if metadata is not None and not isinstance(metadata, dict):
        raise ValidationError("metadata must be an object")
    return {
        "name": name,
        "slug": slug,
        "organization_id": org_id,
        "metadata": dict(metadata or {}),
    }


def validate_create_team(payload: dict[str, Any]) -> dict[str, Any]:
    name = require_non_empty(payload.get("name"), "name", max_len=120)
    org_id = require_non_empty(
        payload.get("organizationId") or payload.get("organization_id"),
        "organizationId",
    )
    slug_raw = payload.get("slug")
    slug = normalize_slug(slug_raw) if slug_raw else normalize_slug(slug_from_name(name))
    workspace_id = payload.get("workspaceId") or payload.get("workspace_id")
    if workspace_id is not None:
        workspace_id = require_non_empty(workspace_id, "workspaceId")
    return {
        "name": name,
        "slug": slug,
        "organization_id": org_id,
        "workspace_id": workspace_id,
    }


def validate_add_member(payload: dict[str, Any]) -> dict[str, Any]:
    org_id = require_non_empty(
        payload.get("organizationId") or payload.get("organization_id"),
        "organizationId",
    )
    user_id = require_non_empty(payload.get("userId") or payload.get("user_id"), "userId")
    role_key = validate_role_key(payload.get("role") or payload.get("roleKey") or "viewer")
    workspace_id = payload.get("workspaceId") or payload.get("workspace_id")
    if workspace_id is not None:
        workspace_id = require_non_empty(workspace_id, "workspaceId")
    return {
        "organization_id": org_id,
        "user_id": user_id,
        "role_key": role_key,
        "workspace_id": workspace_id,
    }


def validate_create_invite(payload: dict[str, Any]) -> dict[str, Any]:
    org_id = require_non_empty(
        payload.get("organizationId") or payload.get("organization_id"),
        "organizationId",
    )
    email = validate_email(payload.get("email"))
    invited_by = require_non_empty(
        payload.get("invitedById") or payload.get("invited_by_id"),
        "invitedById",
    )
    role_key = validate_role_key(payload.get("role") or payload.get("roleKey") or "viewer")
    if role_key == "owner":
        raise ValidationError("cannot invite as owner")
    workspace_id = payload.get("workspaceId") or payload.get("workspace_id")
    if workspace_id is not None:
        workspace_id = require_non_empty(workspace_id, "workspaceId")
    return {
        "organization_id": org_id,
        "email": email,
        "invited_by_id": invited_by,
        "role_key": role_key,
        "workspace_id": workspace_id,
    }

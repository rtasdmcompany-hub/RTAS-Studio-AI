"""Asset types, lifecycle statuses, categories, and creator policies."""

from __future__ import annotations

import re
import secrets
from typing import Final

# Supported AI asset types; "custom" keeps the registry open for future AI assets
ASSET_TYPES: Final[tuple[str, ...]] = (
    "ai_template",
    "prompt_pack",
    "character",
    "voice_model",
    "music_pack",
    "video_template",
    "image_template",
    "workflow_template",
    "automation_pack",
    "custom",
)

ASSET_STATUSES: Final[tuple[str, ...]] = (
    "draft",
    "published",
    "archived",
    "deleted",
)

DEFAULT_CATEGORIES: Final[tuple[str, ...]] = (
    "ai_templates",
    "prompts",
    "characters",
    "voice",
    "music",
    "video",
    "image",
    "workflows",
    "automation",
    "other",
)

CREATOR_TYPES: Final[tuple[str, ...]] = ("creator", "publisher")

CREATOR_STATUSES: Final[tuple[str, ...]] = ("active", "suspended")

VISIBILITY_LEVELS: Final[tuple[str, ...]] = ("public", "organization", "private")

MAX_TAGS_PER_ASSET: Final[int] = 12
MAX_ASSETS_PER_COLLECTION: Final[int] = 200

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def is_semver(value: str) -> bool:
    return bool(_SEMVER_RE.match(value or ""))


def slugify(name: str) -> str:
    slug = _SLUG_RE.sub("-", (name or "").strip().lower()).strip("-")
    return slug or f"asset-{secrets.token_hex(3)}"


def generate_creator_handle(display_name: str) -> str:
    base = slugify(display_name)[:24].strip("-") or "creator"
    return f"{base}-{secrets.token_hex(2)}"

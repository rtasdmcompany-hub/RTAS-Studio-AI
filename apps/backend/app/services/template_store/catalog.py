"""Template types, statuses, categories, sort modes, and integrity helpers."""

from __future__ import annotations

import hashlib
import re
from typing import Final

TEMPLATE_TYPES: Final[tuple[str, ...]] = (
    "video_template",
    "image_template",
    "prompt_template",
    "voice_template",
    "music_template",
    "workflow_template",
    "character_template",
    "brand_template",
    "custom",  # future AI assets
)

TEMPLATE_STATUSES: Final[tuple[str, ...]] = ("active", "archived", "deleted")

DEFAULT_CATEGORIES: Final[tuple[tuple[str, str], ...]] = (
    ("video", "Video"),
    ("image", "Image"),
    ("prompt", "Prompt"),
    ("voice", "Voice"),
    ("music", "Music"),
    ("workflow", "Workflow"),
    ("character", "Character"),
    ("branding", "Branding"),
    ("other", "Other"),
)

SORT_MODES: Final[tuple[str, ...]] = ("latest", "popular", "rating", "featured")

MAX_TAGS_PER_TEMPLATE: Final[int] = 20
MAX_SEARCH_RESULTS: Final[int] = 100

RATING_MIN: Final[int] = 1
RATING_MAX: Final[int] = 5

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_SLUG_STRIP_RE = re.compile(r"[^a-z0-9]+")
_TOKEN_RE = re.compile(r"[a-z0-9]{2,}")


def is_semver(value: str) -> bool:
    return bool(_SEMVER_RE.match(value or ""))


def slugify(value: str) -> str:
    slug = _SLUG_STRIP_RE.sub("-", (value or "").lower()).strip("-")
    return slug or "template"


def tokenize(*texts: str) -> set[str]:
    """Tokenize text fields into lowercase search tokens."""
    tokens: set[str] = set()
    for text in texts:
        tokens.update(_TOKEN_RE.findall((text or "").lower()))
    return tokens


def version_checksum(
    template_id: str, version: str, asset_uri: str, name: str
) -> str:
    """Integrity checksum binding a version to its content pointer."""
    payload = f"{template_id}|{version}|{asset_uri}|{name}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

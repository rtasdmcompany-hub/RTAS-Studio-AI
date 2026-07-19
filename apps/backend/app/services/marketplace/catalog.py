"""Product types, categories, statuses, license and delivery policies."""

from __future__ import annotations

import secrets
from typing import Final

# Supported digital product types; "custom" allows future AI assets
PRODUCT_TYPES: Final[tuple[str, ...]] = (
    "prompt_template",
    "ai_workflow",
    "character",
    "avatar",
    "voice_pack",
    "music_pack",
    "video_template",
    "image_template",
    "brand_kit",
    "logo_pack",
    "lut_pack",
    "preset",
    "custom",
)

PRODUCT_STATUSES: Final[tuple[str, ...]] = (
    "draft",
    "published",
    "archived",
    "deleted",
)

DEFAULT_CATEGORIES: Final[tuple[str, ...]] = (
    "templates",
    "workflows",
    "characters",
    "audio",
    "video",
    "branding",
    "effects",
    "other",
)

PRICING_MODELS: Final[tuple[str, ...]] = ("free", "premium")

PURCHASE_STATUSES: Final[tuple[str, ...]] = (
    "completed",
    "refunded",
)

LICENSE_TYPES: Final[tuple[str, ...]] = (
    "personal",
    "commercial",
    "extended",
)

LICENSE_STATUSES: Final[tuple[str, ...]] = ("active", "revoked")

RATING_MIN: Final[int] = 1
RATING_MAX: Final[int] = 5

# Signed download links expire after this many minutes
DOWNLOAD_LINK_TTL_MINUTES: Final[int] = 30

# Trending window (days) for analytics
TRENDING_WINDOW_DAYS: Final[int] = 7

MAX_TAGS_PER_PRODUCT: Final[int] = 12


def generate_license_key() -> str:
    groups = [secrets.token_hex(2).upper() for _ in range(4)]
    return "RTASMKT-" + "-".join(groups)


def generate_download_token() -> str:
    return secrets.token_urlsafe(32)

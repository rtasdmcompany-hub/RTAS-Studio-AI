"""Creator categories, badges, verification, publishing, and reputation policies."""

from __future__ import annotations

import re
from typing import Any, Final

CREATOR_CATEGORIES: Final[tuple[str, ...]] = (
    "ai_art",
    "video",
    "music",
    "voice",
    "prompts",
    "workflows",
    "automation",
    "branding",
    "education",
    "other",
)

CREATOR_STATUSES: Final[tuple[str, ...]] = ("active", "suspended")

VERIFICATION_STATUSES: Final[tuple[str, ...]] = (
    "unverified",
    "pending",
    "verified",
    "rejected",
)

ASSET_STATUSES: Final[tuple[str, ...]] = (
    "draft",
    "scheduled",
    "published",
    "archived",
    "deleted",
)

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

VISIBILITY_LEVELS: Final[tuple[str, ...]] = ("public", "organization", "private")

ENGAGEMENT_EVENT_TYPES: Final[tuple[str, ...]] = (
    "view",
    "download",
    "purchase",
    "rating",
    "review",
)

SOCIAL_PLATFORMS: Final[tuple[str, ...]] = (
    "website",
    "twitter",
    "youtube",
    "instagram",
    "tiktok",
    "github",
    "linkedin",
)

# Badge key -> (label, description)
BADGE_DEFINITIONS: Final[dict[str, tuple[str, str]]] = {
    "verified": ("Verified Creator", "Identity verified by the organization"),
    "first_publish": ("First Publish", "Published a first asset"),
    "prolific_creator": ("Prolific Creator", "Published 10 or more assets"),
    "popular": ("Popular", "Reached 100 asset downloads"),
    "top_rated": ("Top Rated", "Average rating of 4.5+ across 5+ ratings"),
    "rising_star": ("Rising Star", "Gained 10 or more followers"),
}

PROLIFIC_THRESHOLD: Final[int] = 10
POPULAR_DOWNLOADS_THRESHOLD: Final[int] = 100
TOP_RATED_MIN_AVG: Final[float] = 4.5
TOP_RATED_MIN_COUNT: Final[int] = 5
RISING_STAR_FOLLOWERS: Final[int] = 10

MAX_PORTFOLIO_ITEMS: Final[int] = 50
MAX_CATEGORIES_PER_CREATOR: Final[int] = 5

# Engagement score weights
ENGAGEMENT_WEIGHTS: Final[dict[str, float]] = {
    "view": 0.1,
    "download": 1.0,
    "purchase": 3.0,
    "rating": 1.5,
    "review": 2.0,
    "follower": 2.5,
}

RATING_MIN: Final[int] = 1
RATING_MAX: Final[int] = 5

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_HTTPS_RE = re.compile(r"^https://[^\s]+$")


def is_semver(value: str) -> bool:
    return bool(_SEMVER_RE.match(value or ""))


def is_https_url(value: str) -> bool:
    return bool(_HTTPS_RE.match(value or ""))


def compute_reputation(
    *,
    badges: int,
    downloads: int,
    purchases: int,
    avg_rating: float,
    followers: int,
    verified: bool,
) -> float:
    score = (
        badges * 4.0
        + min(downloads, 200) * 0.1
        + min(purchases, 100) * 0.5
        + avg_rating * 6.0
        + min(followers, 100) * 0.2
        + (10.0 if verified else 0.0)
    )
    return round(min(score, 100.0), 2)


def compute_engagement(counts: dict[str, int]) -> float:
    return round(
        sum(ENGAGEMENT_WEIGHTS.get(key, 0.0) * n for key, n in counts.items()), 2
    )


def validate_social_links(links: dict[str, Any]) -> dict[str, str]:
    from app.services.multi_tenant.validation import ValidationError

    cleaned: dict[str, str] = {}
    for platform, url in (links or {}).items():
        key = str(platform).strip().lower()
        if key not in SOCIAL_PLATFORMS:
            raise ValidationError(f"unknown social platform: {platform}")
        value = str(url or "").strip()
        if not value:
            continue
        if not is_https_url(value):
            raise ValidationError(f"social link for {key} must be an https URL")
        cleaned[key] = value
    return cleaned

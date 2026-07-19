"""Community platform policies: engagement, notifications, spam, reputation."""

from __future__ import annotations

import re
from typing import Final

ENGAGEMENT_KINDS: Final[tuple[str, ...]] = ("like", "favorite", "bookmark")

NOTIFICATION_TYPES: Final[tuple[str, ...]] = (
    "follow",
    "review",
    "rating",
    "comment",
    "reply",
    "mention",
    "like",
    "featured",
)

MODERATION_STATUSES: Final[tuple[str, ...]] = ("visible", "flagged", "removed")

ACTIVITY_VERBS: Final[tuple[str, ...]] = (
    "followed",
    "reviewed",
    "rated",
    "commented",
    "replied",
    "liked",
    "favorited",
    "bookmarked",
    "joined",
)

RATING_MIN: Final[int] = 1
RATING_MAX: Final[int] = 5

MAX_COMMENT_LENGTH: Final[int] = 5_000
MAX_REVIEW_LENGTH: Final[int] = 10_000
MAX_BIO_LENGTH: Final[int] = 2_000

# Spam protection: sliding window limits per user
SPAM_WINDOW_SECONDS: Final[int] = 60
SPAM_MAX_POSTS_PER_WINDOW: Final[int] = 10
SPAM_DUPLICATE_WINDOW_SECONDS: Final[int] = 300

# Discovery
TRENDING_WINDOW_HOURS: Final[int] = 72
TRENDING_LIMIT: Final[int] = 10
RECOMMENDED_LIMIT: Final[int] = 10

# Reputation weights (capped at 100)
REPUTATION_VERIFIED_BONUS: Final[float] = 10.0

_MENTION_RE = re.compile(r"@([A-Za-z0-9_\-.]{2,64})")


def extract_mentions(text: str) -> list[str]:
    """Extract @handle mentions from free text."""
    return sorted(set(_MENTION_RE.findall(text or "")))


def compute_reputation(
    *,
    followers: int,
    reviews_written: int,
    comments_written: int,
    likes_received: int,
    verified: bool,
) -> float:
    score = (
        min(followers, 200) * 0.4
        + min(reviews_written, 100) * 1.0
        + min(comments_written, 200) * 0.3
        + min(likes_received, 500) * 0.2
        + (REPUTATION_VERIFIED_BONUS if verified else 0.0)
    )
    return round(min(score, 100.0), 2)

"""License tiers, API key scopes, rate-limit policies, and platform metadata."""

from __future__ import annotations

import secrets
import string
from typing import Any, Final

LICENSE_TIERS: Final[tuple[str, ...]] = (
    "free",
    "trial",
    "starter",
    "professional",
    "business",
    "enterprise",
)

LICENSE_STATUSES: Final[tuple[str, ...]] = (
    "active",
    "expired",
    "suspended",
    "revoked",
)

# Tier duration in days (0 = perpetual until revoked)
LICENSE_DURATION_DAYS: Final[dict[str, int]] = {
    "free": 0,
    "trial": 14,
    "starter": 365,
    "professional": 365,
    "business": 365,
    "enterprise": 365,
}

API_KEY_TYPES: Final[tuple[str, ...]] = ("personal", "organization", "workspace")
API_KEY_ACCESS: Final[tuple[str, ...]] = ("read_only", "full_access", "scoped")

API_SCOPES: Final[tuple[str, ...]] = (
    "generate:read",
    "generate:write",
    "assets:read",
    "assets:write",
    "projects:read",
    "projects:write",
    "billing:read",
    "analytics:read",
    "webhooks:manage",
)

# Rate limits per license tier: (per minute, per hour, per day); 0 = unlimited
RATE_LIMIT_POLICIES: Final[dict[str, dict[str, int]]] = {
    "free": {"perMinute": 10, "perHour": 100, "perDay": 500},
    "trial": {"perMinute": 20, "perHour": 300, "perDay": 1_500},
    "starter": {"perMinute": 60, "perHour": 1_000, "perDay": 10_000},
    "professional": {"perMinute": 120, "perHour": 5_000, "perDay": 50_000},
    "business": {"perMinute": 300, "perHour": 15_000, "perDay": 150_000},
    "enterprise": {"perMinute": 0, "perHour": 0, "perDay": 0},  # unlimited
}

# Workspace-level limits are a fraction of the organization tier limits
WORKSPACE_LIMIT_FRACTION: Final[float] = 0.5

WEBHOOK_EVENTS: Final[tuple[str, ...]] = (
    "generation.completed",
    "generation.failed",
    "credits.low",
    "invoice.paid",
    "invoice.failed",
    "subscription.renewed",
    "subscription.expired",
    "payout.paid",
)

WEBHOOK_MAX_RETRIES: Final[int] = 5
WEBHOOK_RETRY_BACKOFF_MINUTES: Final[tuple[int, ...]] = (1, 5, 30, 120, 720)

PAT_DEFAULT_EXPIRY_DAYS: Final[int] = 90

API_DOCS_METADATA: Final[dict[str, Any]] = {
    "title": "RTAS Studio AI API",
    "version": "1.0.0",
    "baseUrl": "https://rtas-studio-ai-api.vercel.app/api",
    "specFormat": "openapi-3.1",
    "docsUrl": "https://rtasstudio.ai/docs/api",
    "categories": [
        "generation",
        "assets",
        "projects",
        "billing",
        "credits",
        "analytics",
        "webhooks",
    ],
}

SDK_METADATA: Final[list[dict[str, Any]]] = [
    {"language": "python", "package": "rtas-studio", "version": "1.0.0", "registry": "pypi"},
    {"language": "typescript", "package": "@rtas/studio", "version": "1.0.0", "registry": "npm"},
    {"language": "go", "package": "github.com/rtas/studio-go", "version": "1.0.0", "registry": "go"},
]

_KEY_ALPHABET: Final[str] = string.ascii_letters + string.digits


def generate_secret(length: int = 40) -> str:
    return "".join(secrets.choice(_KEY_ALPHABET) for _ in range(length))


def generate_license_key() -> str:
    groups = ["".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4)) for _ in range(4)]
    return "RTAS-" + "-".join(groups)


def rate_policy(tier: str) -> dict[str, int]:
    return dict(RATE_LIMIT_POLICIES.get(tier, RATE_LIMIT_POLICIES["free"]))

"""Referral / affiliate program rules, commission rates, and payout policy."""

from __future__ import annotations

import secrets
import string
from typing import Final

REFERRAL_STATUSES: Final[tuple[str, ...]] = (
    "invited",
    "signed_up",
    "converted",
    "rewarded",
)

AFFILIATE_STATUSES: Final[tuple[str, ...]] = (
    "pending",
    "active",
    "suspended",
    "rejected",
)

COMMISSION_TYPES: Final[tuple[str, ...]] = ("percentage", "fixed")
COMMISSION_KINDS: Final[tuple[str, ...]] = ("one_time", "recurring")
COMMISSION_STATUSES: Final[tuple[str, ...]] = (
    "pending",
    "approved",
    "paid",
    "rejected",
)

PAYOUT_STATUSES: Final[tuple[str, ...]] = (
    "requested",
    "approved",
    "rejected",
    "paid",
)

# Referral rewards (credits)
REFERRER_REWARD_CREDITS: Final[int] = 100
REFERRED_BONUS_CREDITS: Final[int] = 50

# Commission defaults
DEFAULT_COMMISSION_PCT: Final[float] = 20.0
DEFAULT_FIXED_COMMISSION_USD: Final[float] = 10.0
RECURRING_COMMISSION_PCT: Final[float] = 10.0

# Multi-level commission: level -> share of base commission rate (percent of sale)
MULTI_LEVEL_RATES_PCT: Final[dict[int, float]] = {1: 20.0, 2: 5.0}
MAX_COMMISSION_LEVELS: Final[int] = 2

# Payout policy
MIN_PAYOUT_THRESHOLD_USD: Final[float] = 50.0
PAYOUT_METHODS: Final[tuple[str, ...]] = ("paypal", "bank_transfer", "credits")

REFERRAL_LINK_BASE: Final[str] = "https://rtasstudio.ai/r/"
AFFILIATE_LINK_BASE: Final[str] = "https://rtasstudio.ai/a/"

_CODE_ALPHABET: Final[str] = string.ascii_uppercase + string.digits


def generate_code(prefix: str = "RTAS", length: int = 8) -> str:
    body = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))
    return f"{prefix}-{body}"


def level_rate_pct(level: int) -> float:
    return MULTI_LEVEL_RATES_PCT.get(level, 0.0)

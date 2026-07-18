"""Paddle products, prices, and webhook event catalog."""

from __future__ import annotations

import os
from typing import Any, Final

WEBHOOK_EVENTS: Final[tuple[str, ...]] = (
    "transaction.completed",
    "subscription.created",
    "subscription.updated",
    "subscription.canceled",
    "subscription.cancelled",  # Paddle spelling variant
    "subscription.resumed",
    "subscription.past_due",
    "payment.failed",
    "payment.succeeded",
    "refund.created",
    "refund.completed",
)

# Default price IDs (overridable via env) — map RTAS plan keys → Paddle price IDs
_DEFAULT_PRICE_MAP: Final[dict[str, dict[str, str]]] = {
    "free_trial": {"monthly": "pri_trial_monthly", "yearly": "pri_trial_yearly"},
    "starter": {"monthly": "pri_starter_monthly", "yearly": "pri_starter_yearly"},
    "professional": {"monthly": "pri_pro_monthly", "yearly": "pri_pro_yearly"},
    "business": {"monthly": "pri_business_monthly", "yearly": "pri_business_yearly"},
    "enterprise": {"monthly": "pri_enterprise_monthly", "yearly": "pri_enterprise_yearly"},
}

_ENV_PRICE_KEYS: Final[dict[str, dict[str, str]]] = {
    "starter": {
        "monthly": "PADDLE_STARTER_PRICE_ID",
        "yearly": "PADDLE_STARTER_YEARLY_PRICE_ID",
    },
    "professional": {
        "monthly": "PADDLE_STANDARD_PRICE_ID",
        "yearly": "PADDLE_STANDARD_YEARLY_PRICE_ID",
    },
    "business": {
        "monthly": "PADDLE_PREMIUM_PRICE_ID",
        "yearly": "PADDLE_PREMIUM_YEARLY_PRICE_ID",
    },
    "enterprise": {
        "monthly": "PADDLE_ENTERPRISE_PRICE_ID",
        "yearly": "PADDLE_ENTERPRISE_YEARLY_PRICE_ID",
    },
    "free_trial": {
        "monthly": "PADDLE_TESTER_PRICE_ID",
        "yearly": "PADDLE_TESTER_YEARLY_PRICE_ID",
    },
}


def resolve_price_id(plan_key: str, billing_cycle: str) -> str:
    cycle = "yearly" if billing_cycle in {"yearly", "year", "annual"} else "monthly"
    env_key = (_ENV_PRICE_KEYS.get(plan_key) or {}).get(cycle)
    if env_key:
        value = (os.environ.get(env_key) or "").strip()
        if value:
            return value
    return (_DEFAULT_PRICE_MAP.get(plan_key) or {}).get(cycle) or f"pri_{plan_key}_{cycle}"


def plan_key_from_price_id(price_id: str) -> str | None:
    price_id = (price_id or "").strip()
    if not price_id:
        return None
    for plan_key, cycles in _DEFAULT_PRICE_MAP.items():
        for cycle, pid in cycles.items():
            env_key = (_ENV_PRICE_KEYS.get(plan_key) or {}).get(cycle)
            env_val = (os.environ.get(env_key) or "").strip() if env_key else ""
            if price_id in {pid, env_val}:
                return plan_key
    # Heuristic from custom IDs
    lower = price_id.lower()
    for key in ("enterprise", "business", "professional", "starter", "trial", "tester"):
        if key in lower:
            return "free_trial" if key in {"trial", "tester"} else (
                "professional" if key == "professional" else key
            )
    return None


def product_catalog() -> list[dict[str, Any]]:
    items = []
    for plan_key, cycles in _DEFAULT_PRICE_MAP.items():
        items.append(
            {
                "planKey": plan_key,
                "productId": f"pro_{plan_key}",
                "prices": {
                    "monthly": resolve_price_id(plan_key, "monthly"),
                    "yearly": resolve_price_id(plan_key, "yearly"),
                },
                "defaultPriceIds": cycles,
            }
        )
    return items

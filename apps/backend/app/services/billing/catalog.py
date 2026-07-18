"""Subscription plans, billing cycles, and default limits."""

from __future__ import annotations

from typing import Any, Final

PLAN_KEYS: Final[tuple[str, ...]] = (
    "free_trial",
    "starter",
    "professional",
    "business",
    "enterprise",
)

BILLING_CYCLES: Final[tuple[str, ...]] = ("monthly", "yearly")

SUBSCRIPTION_STATUSES: Final[tuple[str, ...]] = (
    "trialing",
    "active",
    "past_due",
    "canceled",
    "expired",
    "paused",
)

# Plan catalog — monthly price USD, yearly = monthly * 10 (2 months free)
DEFAULT_PLANS: Final[list[dict[str, Any]]] = [
    {
        "key": "free_trial",
        "name": "Free Trial",
        "description": "Evaluate RTAS Studio AI with limited credits",
        "monthlyPriceUsd": 0.0,
        "yearlyPriceUsd": 0.0,
        "creditsMonthly": 100,
        "creditsYearly": 100,
        "maxWorkspaces": 1,
        "maxTeams": 1,
        "maxMembers": 3,
        "maxProjects": 3,
        "aiProviderLimit": 1,
        "features": ["studio_basic", "exports_watermarked", "community_support"],
        "isPublic": True,
        "trialDays": 14,
    },
    {
        "key": "starter",
        "name": "Starter",
        "description": "For solo creators getting started",
        "monthlyPriceUsd": 29.0,
        "yearlyPriceUsd": 290.0,
        "creditsMonthly": 1000,
        "creditsYearly": 12000,
        "maxWorkspaces": 2,
        "maxTeams": 2,
        "maxMembers": 5,
        "maxProjects": 20,
        "aiProviderLimit": 2,
        "features": ["studio_basic", "exports_hd", "email_support"],
        "isPublic": True,
        "trialDays": 0,
    },
    {
        "key": "professional",
        "name": "Professional",
        "description": "For growing production teams",
        "monthlyPriceUsd": 99.0,
        "yearlyPriceUsd": 990.0,
        "creditsMonthly": 5000,
        "creditsYearly": 60000,
        "maxWorkspaces": 10,
        "maxTeams": 10,
        "maxMembers": 25,
        "maxProjects": 100,
        "aiProviderLimit": 4,
        "features": [
            "studio_pro",
            "exports_4k",
            "priority_queue",
            "collaboration",
            "analytics",
        ],
        "isPublic": True,
        "trialDays": 0,
    },
    {
        "key": "business",
        "name": "Business",
        "description": "For agencies and multi-brand studios",
        "monthlyPriceUsd": 299.0,
        "yearlyPriceUsd": 2990.0,
        "creditsMonthly": 20000,
        "creditsYearly": 240000,
        "maxWorkspaces": 50,
        "maxTeams": 50,
        "maxMembers": 100,
        "maxProjects": 500,
        "aiProviderLimit": 8,
        "features": [
            "studio_pro",
            "exports_4k",
            "priority_queue",
            "collaboration",
            "analytics",
            "sso",
            "approvals",
            "dedicated_support",
        ],
        "isPublic": True,
        "trialDays": 0,
    },
    {
        "key": "enterprise",
        "name": "Enterprise",
        "description": "Custom limits, security, and SLA",
        "monthlyPriceUsd": 999.0,
        "yearlyPriceUsd": 9990.0,
        "creditsMonthly": 100000,
        "creditsYearly": 1200000,
        "maxWorkspaces": 500,
        "maxTeams": 500,
        "maxMembers": 2000,
        "maxProjects": 10000,
        "aiProviderLimit": 20,
        "features": [
            "studio_enterprise",
            "exports_unlimited",
            "priority_queue",
            "collaboration",
            "analytics",
            "sso",
            "approvals",
            "audit",
            "sla",
            "dedicated_csm",
        ],
        "isPublic": True,
        "trialDays": 0,
    },
]


def normalize_plan_key(value: str) -> str:
    key = value.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "free": "free_trial",
        "trial": "free_trial",
        "pro": "professional",
        "biz": "business",
    }
    key = aliases.get(key, key)
    if key not in PLAN_KEYS:
        raise ValueError(f"unsupported plan: {value}")
    return key


def normalize_cycle(value: str) -> str:
    key = value.strip().lower()
    aliases = {"month": "monthly", "year": "yearly", "annual": "yearly", "annually": "yearly"}
    key = aliases.get(key, key)
    if key not in BILLING_CYCLES:
        raise ValueError(f"unsupported billing cycle: {value}")
    return key

"""Tax rules, coupon types, invoice statuses, retry policy."""

from __future__ import annotations

from typing import Any, Final

INVOICE_STATUSES: Final[tuple[str, ...]] = (
    "draft",
    "pending",
    "paid",
    "failed",
    "refunded",
    "void",
)

COUPON_TYPES: Final[tuple[str, ...]] = (
    "percentage",
    "fixed",
    "trial",
    "promotional",
    "referral",
)

TAX_TYPES: Final[tuple[str, ...]] = ("vat", "gst", "sales_tax", "none")

# Country → tax type + rate (simplified production catalog)
COUNTRY_TAX_RULES: Final[dict[str, dict[str, Any]]] = {
    "US": {"taxType": "sales_tax", "rate": 0.0725, "name": "US Sales Tax"},
    "GB": {"taxType": "vat", "rate": 0.20, "name": "UK VAT"},
    "DE": {"taxType": "vat", "rate": 0.19, "name": "DE VAT"},
    "FR": {"taxType": "vat", "rate": 0.20, "name": "FR VAT"},
    "AU": {"taxType": "gst", "rate": 0.10, "name": "AU GST"},
    "IN": {"taxType": "gst", "rate": 0.18, "name": "IN GST"},
    "PK": {"taxType": "sales_tax", "rate": 0.17, "name": "PK Sales Tax"},
    "CA": {"taxType": "gst", "rate": 0.05, "name": "CA GST"},
    "AE": {"taxType": "vat", "rate": 0.05, "name": "UAE VAT"},
    "SG": {"taxType": "gst", "rate": 0.09, "name": "SG GST"},
}

DEFAULT_COUPONS: Final[list[dict[str, Any]]] = [
    {
        "code": "WELCOME10",
        "couponType": "percentage",
        "percentOff": 10.0,
        "amountOffUsd": 0.0,
        "maxRedemptions": 1000,
        "perOrgLimit": 1,
        "trialDays": 0,
        "category": "promotional",
    },
    {
        "code": "SAVE25",
        "couponType": "fixed",
        "percentOff": 0.0,
        "amountOffUsd": 25.0,
        "maxRedemptions": 500,
        "perOrgLimit": 1,
        "trialDays": 0,
        "category": "promotional",
    },
    {
        "code": "TRIAL14",
        "couponType": "trial",
        "percentOff": 0.0,
        "amountOffUsd": 0.0,
        "maxRedemptions": 10000,
        "perOrgLimit": 1,
        "trialDays": 14,
        "category": "trial",
    },
    {
        "code": "REFER50",
        "couponType": "referral",
        "percentOff": 50.0,
        "amountOffUsd": 0.0,
        "maxRedemptions": 200,
        "perOrgLimit": 1,
        "trialDays": 0,
        "category": "referral",
    },
]

# Payment retry schedule (hours between attempts)
RETRY_SCHEDULE_HOURS: Final[tuple[int, ...]] = (1, 24, 72)
MAX_PAYMENT_RETRIES: Final[int] = 3

REMINDER_DAYS_BEFORE_RENEWAL: Final[tuple[int, ...]] = (7, 3, 1)


def normalize_country(country: str | None) -> str:
    code = (country or "US").strip().upper()
    if len(code) > 2:
        aliases = {
            "UNITED STATES": "US",
            "USA": "US",
            "UK": "GB",
            "UNITED KINGDOM": "GB",
            "PAKISTAN": "PK",
            "INDIA": "IN",
            "AUSTRALIA": "AU",
            "CANADA": "CA",
            "GERMANY": "DE",
            "FRANCE": "FR",
            "SINGAPORE": "SG",
        }
        code = aliases.get(code, code[:2])
    return code if code in COUNTRY_TAX_RULES else "US"


def tax_rule_for(country: str | None) -> dict[str, Any]:
    return dict(COUNTRY_TAX_RULES[normalize_country(country)])

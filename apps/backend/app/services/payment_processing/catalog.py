"""Credit packs, transaction types, and PayPal event catalog."""

from __future__ import annotations

from typing import Any, Final

CREDIT_TXN_TYPES: Final[tuple[str, ...]] = (
    "purchase",
    "consume",
    "refund",
    "award",
    "bonus",
    "trial",
    "promotional",
    "subscription",
    "adjustment",
    "expire",
)

PAYPAL_WEBHOOK_EVENTS: Final[tuple[str, ...]] = (
    "CHECKOUT.ORDER.APPROVED",
    "PAYMENT.CAPTURE.COMPLETED",
    "PAYMENT.CAPTURE.DENIED",
    "PAYMENT.CAPTURE.REFUNDED",
    "BILLING.SUBSCRIPTION.ACTIVATED",
    "BILLING.SUBSCRIPTION.CANCELLED",
    "PAYMENT.SALE.COMPLETED",
    "PAYMENT.SALE.DENIED",
)

# Credit packs: USD → credits (includes bonus)
CREDIT_PACKS: Final[list[dict[str, Any]]] = [
    {
        "key": "pack_100",
        "name": "Starter Pack",
        "credits": 100,
        "bonusCredits": 0,
        "priceUsd": 9.0,
    },
    {
        "key": "pack_500",
        "name": "Creator Pack",
        "credits": 500,
        "bonusCredits": 50,
        "priceUsd": 39.0,
    },
    {
        "key": "pack_2000",
        "name": "Pro Pack",
        "credits": 2000,
        "bonusCredits": 300,
        "priceUsd": 129.0,
    },
    {
        "key": "pack_10000",
        "name": "Studio Pack",
        "credits": 10000,
        "bonusCredits": 2000,
        "priceUsd": 499.0,
    },
]


def get_pack(pack_key: str) -> dict[str, Any]:
    key = pack_key.strip().lower().replace("-", "_")
    aliases = {"starter": "pack_100", "creator": "pack_500", "pro": "pack_2000", "studio": "pack_10000"}
    key = aliases.get(key, key)
    for pack in CREDIT_PACKS:
        if pack["key"] == key:
            return pack
    raise ValueError(f"unknown credit pack: {pack_key}")


def total_credits(pack: dict[str, Any]) -> int:
    return int(pack["credits"]) + int(pack.get("bonusCredits") or 0)

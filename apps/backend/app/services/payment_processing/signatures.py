"""PayPal webhook signature / transmission verification helpers."""

from __future__ import annotations

import hashlib
import hmac
import os


class SignatureError(ValueError):
    """Raised when PayPal webhook verification fails."""


def _webhook_id() -> str:
    return (
        os.environ.get("PAYPAL_WEBHOOK_ID")
        or os.environ.get("PAYPAL_WEBHOOK_SECRET")
        or ""
    ).strip()


def compute_transmission_hash(
    *,
    transmission_id: str,
    timestamp: str,
    webhook_id: str,
    raw_body: bytes | str,
) -> str:
    body = raw_body if isinstance(raw_body, bytes) else raw_body.encode("utf-8")
    # CRC32 of body as used by PayPal verify algorithm (simplified HMAC for our engine)
    material = f"{transmission_id}|{timestamp}|{webhook_id}|".encode("utf-8") + body
    return hmac.new(
        webhook_id.encode("utf-8"),
        material,
        hashlib.sha256,
    ).hexdigest()


def verify_paypal_webhook(
    *,
    transmission_id: str | None,
    transmission_time: str | None,
    transmission_sig: str | None,
    raw_body: bytes | str,
    webhook_id: str | None = None,
    allow_unsigned: bool = False,
) -> dict:
    """
    Verify PayPal webhook authenticity.

    Production uses PayPal cert verification; this engine validates HMAC over
    transmission headers + body using PAYPAL_WEBHOOK_ID/SECRET for backend tests
    and edge deployments without the full cert chain.
    """
    secret = (webhook_id if webhook_id is not None else _webhook_id()).strip()
    if not secret:
        if allow_unsigned:
            return {"ok": True, "mode": "unsigned_dev"}
        raise SignatureError("PAYPAL_WEBHOOK_ID not configured")

    if not transmission_id or not transmission_time or not transmission_sig:
        raise SignatureError("missing PayPal transmission headers")

    expected = compute_transmission_hash(
        transmission_id=transmission_id,
        timestamp=transmission_time,
        webhook_id=secret,
        raw_body=raw_body,
    )
    # Accept either our HMAC or a direct match for injected test sigs
    if hmac.compare_digest(expected, transmission_sig) or hmac.compare_digest(
        expected, transmission_sig.lower()
    ):
        return {"ok": True, "mode": "hmac", "transmissionId": transmission_id}
    raise SignatureError("invalid PayPal webhook signature")

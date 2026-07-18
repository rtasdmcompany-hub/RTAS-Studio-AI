"""Paddle webhook signature verification (Billing API HMAC-SHA256)."""

from __future__ import annotations

import hashlib
import hmac
import os
import time


class SignatureError(ValueError):
    """Raised when a Paddle webhook signature is missing or invalid."""


def _webhook_secret() -> str:
    return (
        os.environ.get("PADDLE_WEBHOOK_SECRET")
        or os.environ.get("PADDLE_NOTIFICATION_SECRET")
        or ""
    ).strip()


def parse_paddle_signature(header: str | None) -> tuple[str | None, str | None]:
    """Parse `Paddle-Signature: ts=...;h1=...`."""
    if not header:
        return None, None
    ts = h1 = None
    for part in header.split(";"):
        part = part.strip()
        if part.startswith("ts="):
            ts = part[3:].strip()
        elif part.startswith("h1="):
            h1 = part[3:].strip()
    return ts, h1


def build_signed_payload(ts: str, raw_body: bytes | str) -> bytes:
    body = raw_body if isinstance(raw_body, bytes) else raw_body.encode("utf-8")
    return ts.encode("utf-8") + b":" + body


def compute_signature(secret: str, ts: str, raw_body: bytes | str) -> str:
    signed = build_signed_payload(ts, raw_body)
    return hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()


def verify_paddle_signature(
    header: str | None,
    raw_body: bytes | str,
    *,
    secret: str | None = None,
    max_age_sec: int = 300,
    allow_unsigned_in_tests: bool = False,
) -> dict:
    """
    Verify Paddle webhook signature.

    When no secret is configured:
    - allow_unsigned_in_tests=True → accept (dev/test)
    - otherwise → reject
    """
    secret = (secret if secret is not None else _webhook_secret()).strip()
    ts, h1 = parse_paddle_signature(header)

    if not secret:
        if allow_unsigned_in_tests:
            return {"ok": True, "mode": "unsigned_dev", "ts": ts, "h1": h1}
        raise SignatureError("PADDLE_WEBHOOK_SECRET not configured")

    if not ts or not h1:
        raise SignatureError("missing Paddle-Signature header")

    try:
        ts_int = int(ts)
    except ValueError as exc:
        raise SignatureError("invalid signature timestamp") from exc

    if max_age_sec > 0 and abs(int(time.time()) - ts_int) > max_age_sec:
        raise SignatureError("signature timestamp outside allowed window")

    expected = compute_signature(secret, ts, raw_body)
    if not hmac.compare_digest(expected, h1):
        raise SignatureError("invalid webhook signature")

    return {"ok": True, "mode": "hmac", "ts": ts, "h1": h1}

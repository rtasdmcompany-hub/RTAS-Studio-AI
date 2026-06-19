"""Free-tier anti-abuse checks (shared trial-claims.json with Next.js)."""

from __future__ import annotations

import json
from pathlib import Path

BackendRoot = Path(__file__).resolve().parents[2]
TrialClaimsFile = BackendRoot.parent / "web" / ".data" / "trial-claims.json"

FREE_TRIAL_ABUSE_MESSAGE = (
    "Free trial limit reached for this device/network. "
    "Please upgrade to the Premium Plan to continue."
)


def _read_claims() -> list[dict]:
    if not TrialClaimsFile.is_file():
        return []
    try:
        data = json.loads(TrialClaimsFile.read_text(encoding="utf-8"))
        claims = data.get("claims", [])
        return claims if isinstance(claims, list) else []
    except Exception:
        return []


def is_free_trial_blocked(
    *,
    user_id: str,
    ip_address: str | None,
    device_fingerprint: str | None,
    account_trial_used: bool,
) -> tuple[bool, str | None]:
    if account_trial_used:
        return True, "account"

    ip = (ip_address or "").strip()
    fingerprint = (device_fingerprint or "").strip()
    claims = _read_claims()

    if ip and any(c.get("ipAddress") == ip for c in claims):
        return True, "ip"
    if fingerprint and any(c.get("deviceFingerprint") == fingerprint for c in claims):
        return True, "device"
    if any(c.get("userId") == user_id for c in claims):
        return True, "account"

    return False, None

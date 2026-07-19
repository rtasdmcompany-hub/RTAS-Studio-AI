"""Signed download URLs and access validation."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

from app.services.audio_export.models import DownloadTicket

def _sign(payload: str) -> str:
    from app.core.signing_secrets import export_signing_secret

    return hmac.new(
        export_signing_secret(), payload.encode(), hashlib.sha256
    ).hexdigest()[:32]


def create_signed_download(
    export_job_id: str,
    *,
    package_url: str,
    expire_hours: float = 24.0,
    max_downloads: int = 10,
) -> DownloadTicket:
    expires_at = time.time() + max(60.0, float(expire_hours) * 3600.0)
    token = _sign(f"{export_job_id}|{expires_at}|{package_url}")
    ticket_id = f"dl_{hashlib.sha1(f'{export_job_id}|{token}'.encode()).hexdigest()[:10]}"
    signed_url = f"{package_url}?token={token}&exp={int(expires_at)}&job={export_job_id}"
    return DownloadTicket(
        ticket_id=ticket_id,
        export_job_id=export_job_id,
        signed_url=signed_url,
        expires_at=expires_at,
        authorized=True,
        download_count=0,
        max_downloads=max_downloads,
        token=token,
    )


def validate_download(
    *,
    export_job_id: str,
    token: str,
    expires_at: float,
    package_url: str,
    download_count: int = 0,
    max_downloads: int = 10,
    now: float | None = None,
) -> dict[str, Any]:
    current = now if now is not None else time.time()
    expected = _sign(f"{export_job_id}|{expires_at}|{package_url}")
    if not token or not hmac.compare_digest(token, expected):
        return {"ok": False, "authorized": False, "error": "invalid_token"}
    if current > float(expires_at):
        return {"ok": False, "authorized": False, "error": "expired"}
    if download_count >= max_downloads:
        return {"ok": False, "authorized": False, "error": "download_limit"}
    return {
        "ok": True,
        "authorized": True,
        "export_job_id": export_job_id,
        "expires_at": expires_at,
        "remaining_downloads": max_downloads - download_count,
    }

"""
Fal.ai API key presence and validity checks (startup + health).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.core.errors import (
    FAL_AUTH_USER_MESSAGE,
    FAL_CREDIT_USER_MESSAGE,
    is_fal_auth_failure,
    is_fal_credit_failure,
)
from app.services.fal_guard import note_from_http_response

logger = logging.getLogger(__name__)

_startup_result: FalVerifyResult | None = None


@dataclass
class FalVerifyResult:
    configured: bool
    valid: bool | None = None
    error: str | None = None

    @property
    def live_generation_enabled(self) -> bool:
        return self.configured and self.valid is True


def verify_fal_key_sync() -> FalVerifyResult:
    if not settings.fal_configured:
        return FalVerifyResult(configured=False, valid=None)

    key = str(settings.fal_key).strip()
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                "https://queue.fal.run/fal-ai/wan/v2.7/text-to-video",
                headers={
                    "Authorization": f"Key {key}",
                    "Content-Type": "application/json",
                },
                json={},
            )
        body = response.text or ""
        if is_fal_credit_failure(body, response.status_code):
            note_from_http_response(response.status_code, body)
            return FalVerifyResult(
                configured=True,
                valid=False,
                error=FAL_CREDIT_USER_MESSAGE,
            )
        if response.status_code == 403 and is_fal_credit_failure(body, response.status_code):
            note_from_http_response(response.status_code, body)
            return FalVerifyResult(
                configured=True,
                valid=False,
                error=FAL_CREDIT_USER_MESSAGE,
            )
        if response.status_code == 401 or is_fal_auth_failure(body, response.status_code):
            note_from_http_response(response.status_code, body)
            return FalVerifyResult(
                configured=True,
                valid=False,
                error=FAL_AUTH_USER_MESSAGE,
            )
        if response.status_code in (400, 422):
            return FalVerifyResult(configured=True, valid=True)
        if response.status_code < 500:
            return FalVerifyResult(configured=True, valid=True)
        return FalVerifyResult(
            configured=True,
            valid=False,
            error=f"Fal API HTTP {response.status_code}",
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            return FalVerifyResult(
                configured=True,
                valid=False,
                error=FAL_AUTH_USER_MESSAGE,
            )
        return FalVerifyResult(
            configured=True,
            valid=False,
            error=f"Fal API HTTP {exc.response.status_code}",
        )
    except Exception as exc:
        return FalVerifyResult(
            configured=True,
            valid=False,
            error=str(exc),
        )


async def verify_fal_key() -> FalVerifyResult:
    return await asyncio.to_thread(verify_fal_key_sync)


def log_fal_startup_status(result: FalVerifyResult) -> None:
    if not result.configured:
        logger.info(
            "FAL_KEY not set — using local simulation / preview sample. "
            "Paste key in apps/backend/.env or apps/api/.env."
        )
        return

    if result.valid:
        logger.info("FAL_KEY verified — live Fal.ai video generation enabled")
        return

    logger.error(
        "FAL_KEY is set but INVALID: %s — update .env and retry",
        result.error,
    )


async def run_startup_verification() -> FalVerifyResult:
    global _startup_result
    _startup_result = await verify_fal_key()
    log_fal_startup_status(_startup_result)
    return _startup_result


def get_startup_verify_result() -> FalVerifyResult | None:
    return _startup_result

"""
Replicate API token presence and validity checks (startup + health).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.core.errors import REPLICATE_AUTH_USER_MESSAGE

logger = logging.getLogger(__name__)

_startup_result: ReplicateVerifyResult | None = None


@dataclass
class ReplicateVerifyResult:
    configured: bool
    valid: bool | None = None
    username: str | None = None
    error: str | None = None

    @property
    def live_generation_enabled(self) -> bool:
        return self.configured and self.valid is True


def verify_replicate_token_sync() -> ReplicateVerifyResult:
    if not settings.replicate_configured:
        return ReplicateVerifyResult(configured=False, valid=None)

    token = str(settings.replicate_api_token).strip()
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(
                "https://api.replicate.com/v1/account",
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.status_code == 401:
            return ReplicateVerifyResult(
                configured=True,
                valid=False,
                error=REPLICATE_AUTH_USER_MESSAGE,
            )
        response.raise_for_status()
        data = response.json()
        username = data.get("username") if isinstance(data, dict) else None
        return ReplicateVerifyResult(
            configured=True,
            valid=True,
            username=str(username) if username else None,
        )
    except httpx.HTTPStatusError as exc:
        return ReplicateVerifyResult(
            configured=True,
            valid=False,
            error=f"Replicate API HTTP {exc.response.status_code}",
        )
    except httpx.TimeoutException:
        return ReplicateVerifyResult(
            configured=True,
            valid=None,
            error="Replicate verification timed out (network).",
        )
    except httpx.RequestError as exc:
        return ReplicateVerifyResult(
            configured=True,
            valid=None,
            error=f"Replicate verification unavailable: {exc}",
        )
    except Exception as exc:
        return ReplicateVerifyResult(
            configured=True,
            valid=False,
            error=str(exc),
        )


async def verify_replicate_token() -> ReplicateVerifyResult:
    return await asyncio.to_thread(verify_replicate_token_sync)


def log_replicate_startup_status(result: ReplicateVerifyResult) -> None:
    if not result.configured:
        logger.info(
            "REPLICATE_API_TOKEN not set — using local simulation / preview sample. "
            "Paste token in apps/backend/.env line 11."
        )
        return

    if result.valid:
        user = result.username or "unknown"
        logger.info(
            "REPLICATE_API_TOKEN verified — live cloud video generation enabled (user=%s)",
            user,
        )
        return

    if result.valid is None:
        logger.warning(
            "REPLICATE_API_TOKEN check unavailable at startup: %s",
            result.error or "unknown reason",
        )
        return

    logger.error(
        "REPLICATE_API_TOKEN is set but INVALID: %s — "
        "update apps/backend/.env and restart the API",
        result.error,
    )


async def run_startup_verification() -> ReplicateVerifyResult:
    global _startup_result
    # Never block API startup for token verification.
    try:
        _startup_result = await asyncio.wait_for(verify_replicate_token(), timeout=12.0)
    except TimeoutError:
        _startup_result = ReplicateVerifyResult(
            configured=settings.replicate_configured,
            valid=None,
            error="Replicate verification exceeded startup timeout.",
        )
    log_replicate_startup_status(_startup_result)
    return _startup_result


def get_startup_verify_result() -> ReplicateVerifyResult | None:
    return _startup_result

"""
Protect owner Fal.ai wallet from repeat charges on failed / retried generations.

- Blocks live Fal calls after billing/auth failures (persisted to disk).
- Cooldown between live attempts so customer retries do not drain balance.
- Owner can reset after topping up Fal billing.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.core.config import BackendRoot, reload_settings, settings
from app.core.errors import (
    FAL_AUTH_USER_MESSAGE,
    FAL_CREDIT_USER_MESSAGE,
    is_fal_auth_failure,
    is_fal_credit_failure,
)

logger = logging.getLogger(__name__)

_GUARD_PATH = BackendRoot / "data" / "fal-guard.json"
_OWNER_BLOCK_MESSAGE = (
    "RTAS cloud video is paused to protect your Fal.ai balance. "
    "Add credit at https://fal.ai/dashboard/billing, then reset the guard "
    "(restart API after top-up, or POST /api/admin/fal/reset-guard)."
)


@dataclass
class FalGuardState:
    billing_blocked: bool = False
    blocked_reason: str | None = None
    blocked_error_code: str | None = None
    last_failure_at: float | None = None
    last_success_at: float | None = None
    failure_count: int = 0
    cooldown_until: float = 0.0

    def to_public_dict(self) -> dict[str, Any]:
        now = time.time()
        retry_after = max(0, int(self.cooldown_until - now))
        return {
            "billing_blocked": self.billing_blocked,
            "blocked_reason": self.blocked_reason,
            "blocked_error_code": self.blocked_error_code,
            "failure_count": self.failure_count,
            "retry_after_sec": retry_after,
            "live_calls_allowed": self._live_allowed_now(now),
        }

    def _live_allowed_now(self, now: float) -> bool:
        if not reload_settings().fal_live_enabled:
            return False
        if self.billing_blocked:
            return False
        return now >= self.cooldown_until


_state = FalGuardState()


def _load() -> FalGuardState:
    global _state
    if not _GUARD_PATH.is_file():
        _state = FalGuardState()
        return _state
    try:
        raw = json.loads(_GUARD_PATH.read_text(encoding="utf-8"))
        _state = FalGuardState(
            billing_blocked=bool(raw.get("billing_blocked")),
            blocked_reason=raw.get("blocked_reason"),
            blocked_error_code=raw.get("blocked_error_code"),
            last_failure_at=raw.get("last_failure_at"),
            last_success_at=raw.get("last_success_at"),
            failure_count=int(raw.get("failure_count") or 0),
            cooldown_until=float(raw.get("cooldown_until") or 0),
        )
    except Exception as exc:
        logger.warning("Could not read fal guard state: %s", exc)
    return _state


def _save() -> None:
    _GUARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    _GUARD_PATH.write_text(
        json.dumps(asdict(_state), indent=2),
        encoding="utf-8",
    )


def get_guard_state() -> FalGuardState:
    return _load()


def get_guard_public_status() -> dict[str, Any]:
    state = get_guard_state()
    fresh = reload_settings()
    pub = state.to_public_dict()
    pub["live_enabled"] = fresh.fal_live_enabled
    pub["cooldown_sec"] = fresh.fal_retry_cooldown_sec
    return pub


def record_fal_success() -> None:
    state = get_guard_state()
    state.last_success_at = time.time()
    state.cooldown_until = 0.0
    if state.billing_blocked:
        state.billing_blocked = False
        state.blocked_reason = None
        state.blocked_error_code = None
        state.failure_count = 0
        logger.info("Fal guard: billing block cleared after successful generation")
    _save()


def clear_billing_block_if_fal_valid(valid: bool) -> bool:
    """After owner tops up Fal billing, drop persisted block when key verifies OK."""
    if not valid:
        return False
    state = get_guard_state()
    if not state.billing_blocked:
        return False
    reset_guard()
    logger.info("Fal guard: billing block cleared after Fal key re-verified OK")
    return True


def record_fal_failure(
    message: str,
    error_code: str | None = None,
    *,
    block_billing: bool = False,
) -> None:
    state = get_guard_state()
    fresh = reload_settings()
    now = time.time()
    state.last_failure_at = now
    state.failure_count += 1
    state.cooldown_until = now + max(30, fresh.fal_retry_cooldown_sec)
    state.blocked_reason = message
    state.blocked_error_code = error_code

    if block_billing or error_code in ("fal_credit", "fal_auth"):
        state.billing_blocked = True
        if error_code == "fal_credit":
            state.blocked_reason = FAL_CREDIT_USER_MESSAGE
        elif error_code == "fal_auth":
            state.blocked_reason = FAL_AUTH_USER_MESSAGE

    if (
        fresh.fal_strict_billing_guard
        and state.failure_count >= fresh.fal_max_failures_before_block
    ):
        state.billing_blocked = True
        if not state.blocked_reason:
            state.blocked_reason = _OWNER_BLOCK_MESSAGE

    _save()
    logger.warning(
        "Fal guard: failure #%s code=%s blocked=%s cooldown=%ss",
        state.failure_count,
        error_code,
        state.billing_blocked,
        fresh.fal_retry_cooldown_sec,
    )


def classify_and_record_fal_failure(message: str, status_code: int | None = None) -> str:
    if is_fal_credit_failure(message, status_code):
        record_fal_failure(message, "fal_credit", block_billing=True)
        return FAL_CREDIT_USER_MESSAGE
    if is_fal_auth_failure(message, status_code):
        record_fal_failure(message, "fal_auth", block_billing=True)
        return FAL_AUTH_USER_MESSAGE
    record_fal_failure(message, None, block_billing=False)
    return message


def reset_guard() -> dict[str, Any]:
    global _state
    _state = FalGuardState()
    if _GUARD_PATH.is_file():
        _GUARD_PATH.unlink(missing_ok=True)
    logger.info("Fal guard reset — live Fal calls allowed again after owner action")
    return get_guard_public_status()


def assert_fal_live_allowed(user_id: str | None = None) -> None:
    """
    Raise ValueError with user-safe message if a live Fal call must NOT run.
    Call this before any Fal upload/subscribe to protect owner wallet.
    """
    fresh = reload_settings()
    if not fresh.fal_configured:
        return

    if not fresh.fal_live_enabled:
        raise ValueError(
            "Live Fal.ai generation is disabled by the owner (FAL_LIVE_ENABLED=false). "
            "No Fal charges were made."
        )

    state = get_guard_state()
    now = time.time()

    if state.billing_blocked:
        raise ValueError(state.blocked_reason or _OWNER_BLOCK_MESSAGE)

    if now < state.cooldown_until:
        wait = int(state.cooldown_until - now)
        raise ValueError(
            f"Please wait {wait}s before trying again. "
            "This protects your Fal.ai balance from rapid failed retries."
        )

    if user_id:
        logger.debug("Fal guard: live attempt allowed for user=%s", user_id)


def note_from_http_response(status_code: int, body: str) -> None:
    """Detect Fal billing lock from cheap health-style responses."""
    if is_fal_credit_failure(body, status_code):
        record_fal_failure(body, "fal_credit", block_billing=True)
    elif status_code == 401 and is_fal_auth_failure(body, status_code):
        record_fal_failure(body, "fal_auth", block_billing=True)


_load()

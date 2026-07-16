"""Retry policy for Image-to-Video provider requests."""

from __future__ import annotations

from app.services.image_to_video.models import I2VProviderRequest, RetryPolicy

DEFAULT_RETRY_POLICY = RetryPolicy()


def is_retryable_error(error: str | None, policy: RetryPolicy | None = None) -> bool:
    if not error:
        return False
    pol = policy or DEFAULT_RETRY_POLICY
    lower = error.lower()
    return any(s in lower for s in pol.retryable_error_substrings)


def can_retry(
    request: I2VProviderRequest,
    *,
    policy: RetryPolicy | None = None,
    error: str | None = None,
) -> bool:
    pol = policy or DEFAULT_RETRY_POLICY
    max_attempts = min(request.max_attempts, pol.max_attempts)
    if request.attempts >= max_attempts:
        return False
    err = error if error is not None else request.error
    if err is None:
        return request.attempts < max_attempts
    return is_retryable_error(err, pol)


def next_delay_seconds(
    request: I2VProviderRequest,
    *,
    policy: RetryPolicy | None = None,
) -> float:
    pol = policy or DEFAULT_RETRY_POLICY
    return pol.base_delay_seconds * (pol.backoff_multiplier ** max(0, request.attempts - 1))


def mark_for_retry(
    request: I2VProviderRequest,
    *,
    error: str,
    policy: RetryPolicy | None = None,
) -> bool:
    request.attempts += 1
    request.error = error
    if can_retry(request, policy=policy, error=error):
        request.state = "retrying"
        return True
    request.state = "failed"
    return False

"""Retry + timeout helpers for provider connectors."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable, TypeVar

from app.services.provider_connectors.models import ProviderError, StandardResponse

T = TypeVar("T")


class ProviderTimeoutError(Exception):
    def __init__(self, provider: str, timeout_sec: float):
        self.provider = provider
        self.timeout_sec = timeout_sec
        super().__init__(f"{provider} timed out after {timeout_sec}s")


async def with_timeout(coro: Awaitable[T], *, timeout_sec: float, provider: str) -> T:
    try:
        return await asyncio.wait_for(coro, timeout=timeout_sec)
    except asyncio.TimeoutError as exc:
        raise ProviderTimeoutError(provider, timeout_sec) from exc


async def with_retry(
    factory: Callable[[], Awaitable[StandardResponse]],
    *,
    provider: str,
    max_retries: int = 2,
    backoff_sec: float = 0.15,
) -> StandardResponse:
    last: StandardResponse | None = None
    attempts = max(1, max_retries + 1)
    for attempt in range(1, attempts + 1):
        t0 = time.perf_counter()
        try:
            result = await factory()
            result.latency_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            result.metadata = {**(result.metadata or {}), "attempt": attempt}
            if result.success:
                return result
            last = result
            if result.error and not result.error.retryable:
                return result
        except ProviderTimeoutError as exc:
            last = StandardResponse(
                provider=provider,
                success=False,
                capability="text",
                latency_ms=round((time.perf_counter() - t0) * 1000.0, 3),
                error=ProviderError(
                    code="timeout",
                    message=str(exc),
                    provider=provider,
                    retryable=True,
                ),
                metadata={"attempt": attempt},
            )
        except Exception as exc:
            last = StandardResponse(
                provider=provider,
                success=False,
                capability="text",
                latency_ms=round((time.perf_counter() - t0) * 1000.0, 3),
                error=ProviderError(
                    code="connector_error",
                    message=str(exc),
                    provider=provider,
                    retryable=True,
                    details={"type": type(exc).__name__},
                ),
                metadata={"attempt": attempt},
            )
        if attempt < attempts:
            await asyncio.sleep(backoff_sec * attempt)
    return last or StandardResponse(
        provider=provider,
        success=False,
        capability="text",
        error=ProviderError(code="unknown", message="retry exhausted", provider=provider),
    )

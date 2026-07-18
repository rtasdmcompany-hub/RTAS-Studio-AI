"""Base provider connector interface."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from app.services.provider_connectors.auth import require_auth_or_placeholder
from app.services.provider_connectors.config import ProviderConfig, load_provider_config
from app.services.provider_connectors.models import (
    Capability,
    ProviderError,
    ProviderInfo,
    ProviderStatusState,
    StandardRequest,
    StandardResponse,
)
from app.services.provider_connectors.retry import with_retry, with_timeout


class BaseProviderConnector(ABC):
    provider_id: str = "base"
    display_name: str = "Base"
    version: str = "1.0.0"
    capabilities: tuple[Capability, ...] = ("text",)
    default_priority: int = 100

    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or load_provider_config(self.provider_id)
        self._status: ProviderStatusState = (
            "online" if self.config.enabled else "disabled"
        )
        self._last_latency_ms: float | None = None
        self._last_health_at: str | None = None

    def is_configured(self) -> bool:
        return self.config.api_key_present

    def get_priority(self) -> int:
        return int(self.config.priority or self.default_priority)

    def detect_version(self) -> str:
        return self.version

    def status(self) -> ProviderStatusState:
        if not self.config.enabled:
            return "disabled"
        if self._status == "maintenance":
            return "maintenance"
        if not self.is_configured():
            # Placeholder connectors remain online in simulation mode
            return "online"
        return self._status

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            provider_id=self.provider_id,
            display_name=self.display_name,
            version=self.detect_version(),
            status=self.status(),
            capabilities=list(self.capabilities),
            configured=self.is_configured(),
            priority=self.get_priority(),
            latency_ms=self._last_latency_ms,
            last_health_at=self._last_health_at,
            notes=["placeholder_mode"] if not self.is_configured() else [],
        )

    async def health_check(self) -> dict[str, Any]:
        t0 = time.perf_counter()
        live, _ = require_auth_or_placeholder(self.config)
        # Lightweight probe — no external calls that require billing
        ok = self.config.enabled
        latency = round((time.perf_counter() - t0) * 1000.0, 3)
        self._last_latency_ms = latency
        self._last_health_at = datetime.now(timezone.utc).isoformat()
        if not self.config.enabled:
            self._status = "disabled"
        elif ok:
            self._status = "online"
        return {
            "provider_id": self.provider_id,
            "healthy": ok,
            "status": self.status(),
            "configured": live,
            "placeholder": not live,
            "latency_ms": latency,
            "version": self.detect_version(),
            "checked_at": self._last_health_at,
        }

    async def execute(self, request: StandardRequest) -> StandardResponse:
        if request.capability not in self.capabilities:
            return StandardResponse(
                provider=self.provider_id,
                success=False,
                capability=request.capability,
                error=ProviderError(
                    code="unsupported_capability",
                    message=f"{self.provider_id} does not support {request.capability}",
                    provider=self.provider_id,
                    retryable=False,
                ),
            )
        if not self.config.enabled:
            return StandardResponse(
                provider=self.provider_id,
                success=False,
                capability=request.capability,
                error=ProviderError(
                    code="disabled",
                    message=f"{self.provider_id} is disabled",
                    provider=self.provider_id,
                ),
            )

        timeout = request.timeout_sec or self.config.timeout_sec

        async def _once() -> StandardResponse:
            return await with_timeout(
                self._invoke(request),
                timeout_sec=timeout,
                provider=self.provider_id,
            )

        result = await with_retry(
            _once,
            provider=self.provider_id,
            max_retries=self.config.max_retries,
        )
        self._last_latency_ms = result.latency_ms
        result.provider_version = self.detect_version()
        return result

    @abstractmethod
    async def _invoke(self, request: StandardRequest) -> StandardResponse:
        """Provider-specific invoke. Use placeholder when keys unavailable."""
        ...

    def _placeholder_response(self, request: StandardRequest) -> StandardResponse:
        return StandardResponse(
            provider=self.provider_id,
            success=True,
            capability=request.capability,
            data={
                "mode": "placeholder",
                "echo_prompt": (request.prompt or "")[:200],
                "model": request.model or self.config.default_model,
                "message": f"{self.display_name} placeholder response (API key not configured)",
            },
            provider_version=self.detect_version(),
            metadata={"placeholder": True, "auth": "missing"},
        )

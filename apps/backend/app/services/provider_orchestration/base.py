"""Base Provider Interface — unified contract for all AI providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from app.services.provider_orchestration.models import (
    Capability,
    ProviderCapabilityModel,
    ProviderRecord,
    ProviderStatus,
)


class BaseProviderInterface(ABC):
    """Abstract interface every AI provider must implement."""

    provider_id: str = "base"
    display_name: str = "Base Provider"
    version: str = "1.0.0"
    default_priority: int = 100
    capabilities: tuple[Capability, ...] = ("text",)

    def __init__(self) -> None:
        self._status: ProviderStatus = "offline"
        self._enabled: bool = True
        self._configured: bool = False
        self._priority: int = self.default_priority
        self._health_latency_ms: float | None = None
        self._last_health_at: str | None = None
        self._discovered: bool = False

    def capability_model(self) -> ProviderCapabilityModel:
        return ProviderCapabilityModel(
            capabilities=list(self.capabilities),
            models={cap: [] for cap in self.capabilities},
            max_concurrency=4,
        )

    def get_priority(self) -> int:
        return int(self._priority)

    def set_priority(self, priority: int) -> None:
        self._priority = int(priority)

    def get_status(self) -> ProviderStatus:
        if not self._enabled:
            return "disabled"
        return self._status

    def set_status(self, status: ProviderStatus) -> None:
        self._status = status

    def enable(self) -> None:
        self._enabled = True
        if self._status == "disabled":
            self._status = "online" if self._configured else "offline"

    def disable(self) -> None:
        self._enabled = False
        self._status = "disabled"

    def is_configured(self) -> bool:
        return self._configured

    def set_configured(self, configured: bool) -> None:
        self._configured = bool(configured)
        if self._enabled and self._status not in ("busy", "maintenance", "disabled"):
            self._status = "online" if self._configured else "offline"

    def supports(self, capability: Capability | str) -> bool:
        return capability in self.capabilities

    def to_record(self) -> ProviderRecord:
        return ProviderRecord(
            provider_id=self.provider_id,
            display_name=self.display_name,
            version=self.version,
            status=self.get_status(),
            capabilities=list(self.capabilities),
            priority=self.get_priority(),
            configured=self.is_configured(),
            discovered=self._discovered,
            health_latency_ms=self._health_latency_ms,
            last_health_at=self._last_health_at,
            notes=[] if self._configured else ["awaiting_credentials"],
        )

    async def health_check(self) -> dict[str, Any]:
        """Default health probe — subclasses may override for live checks."""
        import time

        t0 = time.perf_counter()
        healthy = self._enabled
        latency = round((time.perf_counter() - t0) * 1000.0, 3)
        self._health_latency_ms = latency
        self._last_health_at = datetime.now(timezone.utc).isoformat()
        if not self._enabled:
            self._status = "disabled"
        elif self._status == "maintenance":
            healthy = False
        elif self._status == "busy":
            healthy = True
        else:
            # Simulation-friendly: discovered/enabled providers report online without keys
            if self._discovered and self._enabled:
                self._status = "online"
                healthy = True
            else:
                self._status = "online" if self._configured else "offline"
                healthy = self._status == "online"
        return {
            "provider_id": self.provider_id,
            "healthy": healthy,
            "status": self.get_status(),
            "configured": self.is_configured(),
            "latency_ms": latency,
            "version": self.version,
            "checked_at": self._last_health_at,
        }

    @abstractmethod
    async def invoke(self, prompt: str, *, capability: Capability = "text", **kwargs: Any) -> dict[str, Any]:
        """Execute a request through this provider."""
        ...

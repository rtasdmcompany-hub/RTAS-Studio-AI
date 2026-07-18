"""AI Provider Manager — unified orchestration entrypoint."""

from __future__ import annotations

from typing import Any

from app.services.provider_orchestration.base import BaseProviderInterface
from app.services.provider_orchestration.discovery import discover_providers
from app.services.provider_orchestration.health import HealthMonitoringService
from app.services.provider_orchestration.models import Capability
from app.services.provider_orchestration.priority import next_available, sort_by_priority
from app.services.provider_orchestration.registry import ProviderRegistry
from app.services.provider_orchestration.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION


class AIProviderManager:
    """Manages registration, discovery, priority, and health of AI providers."""

    def __init__(self, registry: ProviderRegistry | None = None, *, auto_discover: bool = True):
        self.registry = registry or ProviderRegistry()
        self.health = HealthMonitoringService(self.registry)
        self._discovered = False
        if auto_discover:
            self.discover()

    def register(self, provider: BaseProviderInterface) -> None:
        self.registry.register(provider)

    def unregister(self, provider_id: str) -> bool:
        return self.registry.unregister(provider_id)

    def get(self, provider_id: str) -> BaseProviderInterface | None:
        return self.registry.get(provider_id)

    def discover(self) -> dict[str, Any]:
        result = discover_providers(self.registry)
        self._discovered = True
        return result

    def list_installed(self) -> dict[str, Any]:
        summary = self.registry.summary()
        return {
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "installed_providers": summary["providers"],
            "count": summary["count"],
            "priority_order": [p.provider_id for p in sort_by_priority(self.registry.all())],
            "capabilities_catalog": [
                "text",
                "image",
                "video",
                "audio",
                "music",
                "voice",
                "embedding",
                "vision",
                "translation",
            ],
            "status_catalog": ["online", "offline", "busy", "disabled", "maintenance"],
        }

    async def health_monitor(self) -> dict[str, Any]:
        health = await self.health.check_all()
        return {
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            **health,
        }

    def select_provider(self, capability: Capability | str = "text") -> BaseProviderInterface | None:
        return next_available(self.registry.all(), capability=str(capability))

    async def invoke(
        self,
        prompt: str,
        *,
        capability: Capability = "text",
        provider_id: str | None = None,
    ) -> dict[str, Any]:
        if provider_id:
            provider = self.registry.get(provider_id)
            if not provider:
                raise ValueError(f"Provider not found: {provider_id}")
        else:
            provider = self.select_provider(capability)
            if not provider:
                raise ValueError(f"No available provider for capability: {capability}")
        return await provider.invoke(prompt, capability=capability)


_manager: AIProviderManager | None = None


def get_provider_manager(*, refresh: bool = False) -> AIProviderManager:
    global _manager
    if _manager is None or refresh:
        _manager = AIProviderManager(auto_discover=True)
    return _manager


def reset_provider_manager() -> None:
    global _manager
    _manager = None

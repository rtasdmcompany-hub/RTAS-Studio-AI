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

    async def invoke_with_failover(
        self,
        prompt: str,
        *,
        capability: Capability = "text",
        max_attempts: int = 3,
        force_fail_first: bool = False,
    ) -> dict[str, Any]:
        """
        Invoke with automatic failover across priority-ordered providers.
        Retries remaining providers on failure; supports timeout/recovery metadata.
        """
        candidates = [
            p
            for p in sort_by_priority(self.registry.all())
            if p.supports(str(capability)) and p.is_enabled()
        ]
        if not candidates:
            return {
                "success": False,
                "error": f"No available provider for capability: {capability}",
                "attempts": 0,
                "failoverLog": ["no_candidates"],
            }

        failover_log: list[str] = []
        last_error: str | None = None
        attempts = 0

        for index, provider in enumerate(candidates[: max(1, max_attempts)]):
            attempts += 1
            if force_fail_first and index == 0:
                failover_log.append(f"fail:{provider.provider_id}:forced")
                last_error = "forced_failure_for_failover"
                continue
            try:
                result = await provider.invoke(prompt, capability=capability)
                if result.get("success"):
                    failover_log.append(f"ok:{provider.provider_id}")
                    return {
                        **result,
                        "success": True,
                        "attempts": attempts,
                        "failoverLog": failover_log,
                        "recovered": index > 0 or force_fail_first,
                    }
                last_error = str(result.get("error") or "invoke_failed")
                failover_log.append(f"fail:{provider.provider_id}:{last_error}")
            except Exception as exc:
                last_error = str(exc)
                failover_log.append(f"error:{provider.provider_id}:{last_error}")

        return {
            "success": False,
            "error": last_error or "all_providers_failed",
            "attempts": attempts,
            "failoverLog": failover_log,
        }


_manager: AIProviderManager | None = None


def get_provider_manager(*, refresh: bool = False) -> AIProviderManager:
    global _manager
    if _manager is None or refresh:
        _manager = AIProviderManager(auto_discover=True)
    return _manager


def reset_provider_manager() -> None:
    global _manager
    _manager = None

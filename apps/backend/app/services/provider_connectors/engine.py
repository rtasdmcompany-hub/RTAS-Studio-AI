"""Provider Connector Engine — unified interface for multi-provider ops."""

from __future__ import annotations

from typing import Any

from app.services.provider_connectors.auth import auth_status
from app.services.provider_connectors.health import health_all, health_one
from app.services.provider_connectors.models import Capability, StandardRequest, StandardResponse
from app.services.provider_connectors.registry import ProviderRegistry, get_registry, reset_registry
from app.services.provider_connectors.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION


class ProviderConnectorEngine:
    def __init__(self, registry: ProviderRegistry | None = None):
        self.registry = registry or get_registry()
        if not self.registry.list_ids():
            self.registry.discover()

    def list_providers(self) -> dict[str, Any]:
        summary = self.registry.summary()
        return {
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            **summary,
            "priority_order": [c.provider_id for c in self.registry.by_priority()],
        }

    async def status(self) -> dict[str, Any]:
        health = await health_all(self.registry)
        return {
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "statuses": [
                {
                    **c.info().to_dict(),
                    "auth": auth_status(c.provider_id),
                }
                for c in self.registry.by_priority()
            ],
            "health": health,
        }

    async def test_provider(
        self,
        provider_id: str,
        *,
        prompt: str = "RTAS connector health probe",
        capability: Capability = "text",
    ) -> dict[str, Any]:
        connector = self.registry.get(provider_id)
        if not connector:
            raise ValueError(f"Provider not found: {provider_id}")
        # Pick a supported capability if text unsupported
        cap: Capability = capability
        if cap not in connector.capabilities:
            cap = connector.capabilities[0]
        health = await connector.health_check()
        request = StandardRequest(prompt=prompt, capability=cap, timeout_sec=10.0)
        response: StandardResponse = await connector.execute(request)
        return {
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "provider_id": provider_id,
            "health": health,
            "request": request.to_dict(),
            "response": response.to_dict(),
            "latency_ms": response.latency_ms,
            "provider_version": connector.detect_version(),
            "ok": response.success,
            "secrets_exposed": False,
        }

    async def test_all(self, prompt: str = "RTAS connector health probe") -> dict[str, Any]:
        results = []
        for connector in self.registry.by_priority():
            results.append(
                await self.test_provider(connector.provider_id, prompt=prompt)
            )
        return {
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "results": results,
            "passed": sum(1 for r in results if r.get("ok")),
            "total": len(results),
            "secrets_exposed": False,
        }


_engine: ProviderConnectorEngine | None = None


def get_connector_engine() -> ProviderConnectorEngine:
    global _engine
    if _engine is None:
        reset_registry()
        _engine = ProviderConnectorEngine(get_registry())
    return _engine


def reset_engine() -> None:
    global _engine
    _engine = None
    reset_registry()

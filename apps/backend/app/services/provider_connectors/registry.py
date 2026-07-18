"""Provider registry — registration, discovery, priority."""

from __future__ import annotations

from typing import Any

from app.services.provider_connectors.adapters import BUILTIN_CONNECTORS
from app.services.provider_connectors.base import BaseProviderConnector
from app.services.provider_connectors.config import load_provider_config


class ProviderRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, BaseProviderConnector] = {}

    def register(self, connector: BaseProviderConnector) -> None:
        if not connector or not connector.provider_id:
            raise ValueError("connector.provider_id is required")
        self._connectors[connector.provider_id] = connector

    def unregister(self, provider_id: str) -> bool:
        return self._connectors.pop(provider_id, None) is not None

    def get(self, provider_id: str) -> BaseProviderConnector | None:
        return self._connectors.get((provider_id or "").strip().lower())

    def list_ids(self) -> list[str]:
        return sorted(self._connectors.keys())

    def all(self) -> list[BaseProviderConnector]:
        return [self._connectors[k] for k in sorted(self._connectors.keys())]

    def by_priority(self) -> list[BaseProviderConnector]:
        return sorted(self.all(), key=lambda c: (c.get_priority(), c.provider_id))

    def discover(self) -> list[str]:
        """Automatic discovery of built-in + already registered connectors."""
        discovered: list[str] = []
        for cls in BUILTIN_CONNECTORS:
            pid = cls.provider_id
            if pid not in self._connectors:
                cfg = load_provider_config(pid)
                self.register(cls(cfg))
            discovered.append(pid)
        return sorted(set(discovered) | set(self._connectors.keys()))

    def summary(self) -> dict[str, Any]:
        items = [c.info().to_dict() for c in self.by_priority()]
        return {
            "providers": items,
            "count": len(items),
            "installed": [p["provider_id"] for p in items],
        }


_registry: ProviderRegistry | None = None


def get_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
        _registry.discover()
    return _registry


def reset_registry() -> None:
    global _registry
    _registry = None

"""Automatic provider discovery."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.services.provider_orchestration.builtins import builtin_provider_factories

if TYPE_CHECKING:
    from app.services.provider_orchestration.registry import ProviderRegistry


def discover_providers(registry: "ProviderRegistry") -> dict[str, Any]:
    """Discover and register built-in providers that are not yet installed."""
    discovered: list[str] = []
    newly_registered: list[str] = []
    for factory in builtin_provider_factories():
        provider = factory()
        pid = provider.provider_id
        discovered.append(pid)
        if not registry.has(pid):
            provider._discovered = True
            if provider.get_status() != "disabled":
                provider.set_status("online")
            registry.register(provider)
            newly_registered.append(pid)
        else:
            existing = registry.get(pid)
            if existing:
                existing._discovered = True
    return {
        "discovered": sorted(set(discovered)),
        "newly_registered": sorted(newly_registered),
        "installed_count": registry.count(),
    }

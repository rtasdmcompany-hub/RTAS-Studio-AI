"""Provider Registry — register, lookup, list providers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.provider_orchestration.base import BaseProviderInterface


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, "BaseProviderInterface"] = {}

    def register(self, provider: "BaseProviderInterface") -> None:
        if not provider or not getattr(provider, "provider_id", None):
            raise ValueError("provider.provider_id is required")
        pid = provider.provider_id.strip().lower()
        provider.provider_id = pid
        self._providers[pid] = provider

    def unregister(self, provider_id: str) -> bool:
        return self._providers.pop((provider_id or "").strip().lower(), None) is not None

    def get(self, provider_id: str) -> "BaseProviderInterface | None":
        return self._providers.get((provider_id or "").strip().lower())

    def has(self, provider_id: str) -> bool:
        return (provider_id or "").strip().lower() in self._providers

    def list_ids(self) -> list[str]:
        return sorted(self._providers.keys())

    def all(self) -> list["BaseProviderInterface"]:
        return [self._providers[k] for k in sorted(self._providers.keys())]

    def count(self) -> int:
        return len(self._providers)

    def clear(self) -> None:
        self._providers.clear()

    def summary(self) -> dict[str, Any]:
        from app.services.provider_orchestration.priority import sort_by_priority

        ordered = sort_by_priority(self.all())
        return {
            "providers": [p.to_record().to_dict() for p in ordered],
            "installed": [p.provider_id for p in ordered],
            "count": len(ordered),
        }

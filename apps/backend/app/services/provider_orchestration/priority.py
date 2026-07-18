"""Provider priority system — lower number = higher priority."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.provider_orchestration.base import BaseProviderInterface

# Default priority bands (lower = preferred)
PRIORITY_BANDS = {
    "critical": 10,
    "high": 25,
    "normal": 50,
    "low": 75,
    "fallback": 100,
}


def sort_by_priority(providers: list["BaseProviderInterface"]) -> list["BaseProviderInterface"]:
    return sorted(providers, key=lambda p: (p.get_priority(), p.provider_id))


def assign_priority(provider: "BaseProviderInterface", band: str | int) -> int:
    if isinstance(band, int):
        provider.set_priority(band)
        return band
    value = PRIORITY_BANDS.get((band or "normal").lower(), PRIORITY_BANDS["normal"])
    provider.set_priority(value)
    return value


def next_available(
    providers: list["BaseProviderInterface"],
    *,
    capability: str | None = None,
) -> "BaseProviderInterface | None":
    for provider in sort_by_priority(providers):
        status = provider.get_status()
        if status in ("disabled", "offline", "maintenance"):
            continue
        if capability and not provider.supports(capability):  # type: ignore[arg-type]
            continue
        return provider
    return None

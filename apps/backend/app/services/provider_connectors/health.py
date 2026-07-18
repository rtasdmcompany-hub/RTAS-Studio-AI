"""Health monitoring service for provider connectors."""

from __future__ import annotations

from typing import Any

from app.services.provider_connectors.registry import ProviderRegistry, get_registry


async def health_all(registry: ProviderRegistry | None = None) -> dict[str, Any]:
    reg = registry or get_registry()
    reports = []
    online = 0
    for connector in reg.by_priority():
        report = await connector.health_check()
        reports.append(report)
        if report.get("healthy") and report.get("status") == "online":
            online += 1
    return {
        "reports": reports,
        "online": online,
        "total": len(reports),
        "all_healthy": online == len(reports) and len(reports) > 0,
    }


async def health_one(provider_id: str, registry: ProviderRegistry | None = None) -> dict[str, Any] | None:
    reg = registry or get_registry()
    connector = reg.get(provider_id)
    if not connector:
        return None
    return await connector.health_check()

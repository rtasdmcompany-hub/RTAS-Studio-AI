"""Health monitoring service for orchestrated providers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.provider_orchestration.registry import ProviderRegistry


class HealthMonitoringService:
    def __init__(self, registry: "ProviderRegistry"):
        self.registry = registry

    async def check_all(self) -> dict[str, Any]:
        reports = []
        online = 0
        for provider in self.registry.all():
            report = await provider.health_check()
            reports.append(report)
            if report.get("status") == "online" and report.get("healthy"):
                online += 1
        return {
            "reports": reports,
            "online": online,
            "offline": sum(1 for r in reports if r.get("status") == "offline"),
            "busy": sum(1 for r in reports if r.get("status") == "busy"),
            "disabled": sum(1 for r in reports if r.get("status") == "disabled"),
            "maintenance": sum(1 for r in reports if r.get("status") == "maintenance"),
            "total": len(reports),
            "all_healthy": online == len(reports) and len(reports) > 0,
        }

    async def check_one(self, provider_id: str) -> dict[str, Any] | None:
        provider = self.registry.get(provider_id)
        if not provider:
            return None
        return await provider.health_check()

"""Enterprise Reporting, Analytics & Business Intelligence Engine — Phase 7 Sprint 8."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.analytics_bi import store
from app.services.analytics_bi.catalog import KPI_DEFS, REPORT_TYPES, normalize_report_type
from app.services.analytics_bi.models import (
    AnalyticsRecord,
    BusinessMetric,
    ForecastRecord,
    KpiRecord,
    PerformanceStatistic,
    ReportHistory,
    UsageStatistic,
    new_id,
)
from app.services.analytics_bi.version import (
    CACHE_TTL_SEC,
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    SPRINT,
)
from app.services.enterprise_auth.audit import log_auth_event
from app.services.enterprise_auth.errors import ForbiddenError
from app.services.enterprise_auth.middleware import require_access
from app.services.multi_tenant.repository import get_repository
from app.services.multi_tenant.validation import ValidationError, require_non_empty


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _audit(action: str, actor_id: str, detail: str | None = None, **meta: Any) -> None:
    log_auth_event(
        action,
        actor_id=actor_id,
        success=True,
        detail=detail or action,
        metadata=meta,
    )


def _require_analytics(
    *,
    actor_id: str,
    organization_id: str,
    workspace_id: str | None = None,
) -> None:
    require_access(
        user_id=actor_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        permission="content.read",
    )
    if workspace_id:
        ws = get_repository().get_workspace(workspace_id)
        if ws is None or ws.organization_id != organization_id:
            raise ForbiddenError("workspace isolation violation")


def _require_report_write(
    *,
    actor_id: str,
    organization_id: str,
    workspace_id: str | None = None,
) -> None:
    require_access(
        user_id=actor_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        permission="content.read",
    )
    member = get_repository().get_member_by_org_user(organization_id, actor_id)
    if member is None:
        raise ForbiddenError("report permission denied")
    # viewers can read analytics; generating reports requires write or manager+
    if member.role_key == "viewer":
        raise ForbiddenError("report permission denied")
    if workspace_id:
        ws = get_repository().get_workspace(workspace_id)
        if ws is None or ws.organization_id != organization_id:
            raise ForbiddenError("workspace isolation violation")


class MetricsEngine:
    def ingest(self, payload: dict[str, Any], *, actor_id: str | None = None) -> dict[str, Any]:
        org_id = require_non_empty(
            payload.get("organizationId") or payload.get("organization_id"),
            "organizationId",
        )
        category = str(payload.get("category") or "api").lower()
        key = require_non_empty(payload.get("metricKey") or payload.get("key"), "metricKey", max_len=80)
        value = float(payload.get("metricValue") or payload.get("value") or 1)
        workspace_id = payload.get("workspaceId") or payload.get("workspace_id")
        rec = AnalyticsRecord(
            id=new_id("arec_"),
            organization_id=org_id,
            workspace_id=str(workspace_id) if workspace_id else None,
            category=category,
            metric_key=key,
            metric_value=value,
            dimensions=dict(payload.get("dimensions") or {}),
        )
        store.save_analytics(rec)
        store.bump(org_id, f"{category}.{key}", value)
        store.bump(org_id, key, value)
        if actor_id:
            _audit("analytics.ingested", actor_id, key, organizationId=org_id)
        return {"ok": True, "record": rec.to_dict()}

    def record_usage(self, payload: dict[str, Any]) -> dict[str, Any]:
        org_id = require_non_empty(
            payload.get("organizationId") or payload.get("organization_id"),
            "organizationId",
        )
        usage_type = require_non_empty(
            payload.get("usageType") or payload.get("type"), "usageType", max_len=64
        )
        count = int(payload.get("count") or 1)
        nbytes = int(payload.get("bytes") or 0)
        u = UsageStatistic(
            id=new_id("usage_"),
            organization_id=org_id,
            workspace_id=payload.get("workspaceId") or payload.get("workspace_id"),
            usage_type=usage_type,
            count=count,
            bytes=nbytes,
            metadata=dict(payload.get("metadata") or {}),
        )
        store.save_usage(u)
        store.bump(org_id, f"usage.{usage_type}", count)
        store.bump(org_id, f"usage.{usage_type}.bytes", float(nbytes))
        return {"ok": True, "usage": u.to_dict()}

    def record_performance(self, payload: dict[str, Any]) -> dict[str, Any]:
        org_id = require_non_empty(
            payload.get("organizationId") or payload.get("organization_id"),
            "organizationId",
        )
        key = require_non_empty(payload.get("metricKey") or payload.get("key"), "metricKey")
        p = PerformanceStatistic(
            id=new_id("perf_"),
            organization_id=org_id,
            workspace_id=payload.get("workspaceId") or payload.get("workspace_id"),
            metric_key=key,
            avg_ms=float(payload.get("avgMs") or payload.get("avg_ms") or 0),
            p95_ms=float(payload.get("p95Ms") or payload.get("p95_ms") or 0),
            success_rate=float(payload.get("successRate") or payload.get("success_rate") or 1),
            sample_count=int(payload.get("sampleCount") or payload.get("sample_count") or 1),
            metadata=dict(payload.get("metadata") or {}),
        )
        store.save_perf(p)
        store.bump(org_id, f"perf.{key}.avg_ms", p.avg_ms)
        store.bump(org_id, f"perf.{key}.samples", float(p.sample_count))
        return {"ok": True, "performance": p.to_dict()}


class DashboardDataEngine:
    def build(self, *, organization_id: str, workspace_id: str | None = None) -> dict[str, Any]:
        counters = store.get_counters(organization_id)
        repo = get_repository()
        workspaces = repo.list_workspaces(organization_id)
        teams = repo.list_teams(organization_id, workspace_id=workspace_id)
        members = repo.list_members(organization_id, workspace_id=workspace_id)
        return {
            "organizationId": organization_id,
            "workspaceId": workspace_id,
            "cards": {
                "totalWorkspaces": len(workspaces) if not workspace_id else 1,
                "totalTeams": len(teams),
                "totalUsers": len(members),
                "activeUsers": int(counters.get("active_users", len(members))),
                "activeProjects": int(counters.get("active_projects", counters.get("project.active", 0))),
                "aiJobsCreated": int(counters.get("ai.jobs_created", counters.get("ai_jobs_created", 0))),
                "aiJobsCompleted": int(
                    counters.get("ai.jobs_completed", counters.get("ai_jobs_completed", 0))
                ),
                "failedJobs": int(counters.get("ai.jobs_failed", counters.get("failed_jobs", 0))),
                "storageBytes": int(counters.get("usage.storage.bytes", counters.get("storage_bytes", 0))),
                "apiCalls": int(counters.get("usage.api", counters.get("api_calls", 0))),
                "exports": int(counters.get("usage.export", 0)),
                "downloads": int(counters.get("usage.download", 0)),
            },
            "generatedAt": _now().isoformat().replace("+00:00", "Z"),
        }


class AnalyticsEngine:
    def __init__(self) -> None:
        self.metrics = MetricsEngine()
        self.dashboard = DashboardDataEngine()

    def overview(
        self, *, actor_id: str, organization_id: str, workspace_id: str | None = None
    ) -> dict[str, Any]:
        with store.timed_op("query"):
            _require_analytics(
                actor_id=actor_id, organization_id=organization_id, workspace_id=workspace_id
            )
            cache_key = f"overview:{organization_id}:{workspace_id or '-'}"
            cached = store.cache_get(cache_key)
            if cached is not None:
                return cached
            repo = get_repository()
            org = repo.get_organization(organization_id)
            if org is None:
                member = repo.get_member_by_org_user(organization_id, actor_id)
                if member is None:
                    raise ForbiddenError("organization isolation violation")
            dash = self.dashboard.build(
                organization_id=organization_id, workspace_id=workspace_id
            )
            counters = store.get_counters(organization_id)
            created = float(counters.get("ai.jobs_created", counters.get("ai_jobs_created", 0)))
            completed = float(
                counters.get("ai.jobs_completed", counters.get("ai_jobs_completed", 0))
            )
            failed = float(counters.get("ai.jobs_failed", counters.get("failed_jobs", 0)))
            avg_gen = float(counters.get("perf.generation.avg_ms", 0))
            perfs = [p for p in store.list_perf(organization_id) if p.metric_key == "generation"]
            if perfs:
                avg_gen = perfs[-1].avg_ms
            result = {
                "ok": True,
                "organizationId": organization_id,
                "workspaceId": workspace_id,
                "overview": {
                    "totalOrganizations": 1,
                    "totalWorkspaces": dash["cards"]["totalWorkspaces"],
                    "totalTeams": dash["cards"]["totalTeams"],
                    "totalUsers": dash["cards"]["totalUsers"],
                    "activeUsers": dash["cards"]["activeUsers"],
                    "activeProjects": dash["cards"]["activeProjects"],
                    "aiJobsCreated": int(created),
                    "aiJobsCompleted": int(completed),
                    "failedJobs": int(failed),
                    "averageGenerationTimeMs": round(avg_gen, 2),
                    "queuePerformance": {
                        "pending": int(counters.get("queue.pending", 0)),
                        "throughput": int(counters.get("queue.throughput", completed)),
                    },
                    "providerUsage": dict(
                        {
                            k.replace("provider.", ""): int(v)
                            for k, v in counters.items()
                            if k.startswith("provider.")
                        }
                    ),
                    "assetUsage": int(counters.get("usage.asset", counters.get("asset_usage", 0))),
                    "storageUsageBytes": dash["cards"]["storageBytes"],
                    "apiUsage": dash["cards"]["apiCalls"],
                    "exportStatistics": dash["cards"]["exports"],
                    "downloadStatistics": dash["cards"]["downloads"],
                },
                "dashboard": dash,
                "cached": False,
            }
            store.cache_set(cache_key, {**result, "cached": True}, CACHE_TTL_SEC)
            _audit("analytics.overview", actor_id, organization_id)
            return result

    def organizations(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        data = self.overview(actor_id=actor_id, organization_id=organization_id)
        return {
            "ok": True,
            "organizationId": organization_id,
            "organizations": [
                {
                    "id": organization_id,
                    "workspaces": data["overview"]["totalWorkspaces"],
                    "teams": data["overview"]["totalTeams"],
                    "users": data["overview"]["totalUsers"],
                    "activeProjects": data["overview"]["activeProjects"],
                    "aiJobsCompleted": data["overview"]["aiJobsCompleted"],
                }
            ],
        }

    def projects(
        self, *, actor_id: str, organization_id: str, workspace_id: str | None = None
    ) -> dict[str, Any]:
        data = self.overview(
            actor_id=actor_id, organization_id=organization_id, workspace_id=workspace_id
        )
        counters = store.get_counters(organization_id)
        return {
            "ok": True,
            "activeProjects": data["overview"]["activeProjects"],
            "projectChanges": int(counters.get("project.changes", 0)),
            "versionsCreated": int(counters.get("version.created", 0)),
            "approvals": int(counters.get("approval.count", 0)),
        }

    def ai(
        self, *, actor_id: str, organization_id: str, workspace_id: str | None = None
    ) -> dict[str, Any]:
        data = self.overview(
            actor_id=actor_id, organization_id=organization_id, workspace_id=workspace_id
        )
        o = data["overview"]
        total = max(o["aiJobsCreated"], 1)
        return {
            "ok": True,
            "aiJobsCreated": o["aiJobsCreated"],
            "aiJobsCompleted": o["aiJobsCompleted"],
            "failedJobs": o["failedJobs"],
            "successRate": round(o["aiJobsCompleted"] / total * 100, 2),
            "averageGenerationTimeMs": o["averageGenerationTimeMs"],
            "queuePerformance": o["queuePerformance"],
            "providerUsage": o["providerUsage"],
        }

    def storage(
        self, *, actor_id: str, organization_id: str, workspace_id: str | None = None
    ) -> dict[str, Any]:
        data = self.overview(
            actor_id=actor_id, organization_id=organization_id, workspace_id=workspace_id
        )
        bytes_used = data["overview"]["storageUsageBytes"]
        return {
            "ok": True,
            "storageUsageBytes": bytes_used,
            "storageUsageGb": round(bytes_used / (1024**3), 4),
            "assetUsage": data["overview"]["assetUsage"],
            "exports": data["overview"]["exportStatistics"],
            "downloads": data["overview"]["downloadStatistics"],
        }


class KpiEngine:
    def compute(
        self, *, actor_id: str, organization_id: str, workspace_id: str | None = None
    ) -> dict[str, Any]:
        with store.timed_op("query"):
            _require_analytics(
                actor_id=actor_id, organization_id=organization_id, workspace_id=workspace_id
            )
            analytics = AnalyticsEngine()
            overview = analytics.overview(
                actor_id=actor_id,
                organization_id=organization_id,
                workspace_id=workspace_id,
            )["overview"]
            created = max(overview["aiJobsCreated"], 1)
            success = overview["aiJobsCompleted"] / created * 100
            error_rate = overview["failedJobs"] / created * 100
            values = {
                "active_users": float(overview["activeUsers"]),
                "ai_success_rate": round(success, 2),
                "avg_generation_ms": float(overview["averageGenerationTimeMs"]),
                "active_projects": float(overview["activeProjects"]),
                "storage_gb": round(overview["storageUsageBytes"] / (1024**3), 4),
                "api_error_rate": round(error_rate, 2),
            }
            kpis = []
            for defn in KPI_DEFS:
                key = defn["key"]
                val = values.get(key, 0.0)
                target = float(defn.get("target") or 0)
                prev = store.list_kpis(organization_id)
                prev_map = {k.kpi_key: k.value for k in prev}
                prev_val = prev_map.get(key)
                if prev_val is None:
                    trend = "stable"
                elif val > prev_val:
                    trend = "up"
                elif val < prev_val:
                    trend = "down"
                else:
                    trend = "stable"
                rec = KpiRecord(
                    id=new_id("kpi_"),
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    kpi_key=key,
                    label=defn["label"],
                    value=val,
                    target=target,
                    unit=defn.get("unit"),
                    trend=trend,
                )
                store.save_kpi(rec)
                store.save_business(
                    BusinessMetric(
                        id=new_id("bmet_"),
                        organization_id=organization_id,
                        workspace_id=workspace_id,
                        name=key,
                        value=val,
                        unit=defn.get("unit"),
                        period="realtime",
                    )
                )
                kpis.append(rec.to_dict())
            return {"ok": True, "count": len(kpis), "kpis": kpis}


class BusinessIntelligenceEngine:
    def __init__(self) -> None:
        self.analytics = AnalyticsEngine()
        self.kpis = KpiEngine()

    def insights(
        self, *, actor_id: str, organization_id: str, workspace_id: str | None = None
    ) -> dict[str, Any]:
        with store.timed_op("query"):
            _require_analytics(
                actor_id=actor_id, organization_id=organization_id, workspace_id=workspace_id
            )
            overview = self.analytics.overview(
                actor_id=actor_id,
                organization_id=organization_id,
                workspace_id=workspace_id,
            )["overview"]
            kpi = self.kpis.compute(
                actor_id=actor_id,
                organization_id=organization_id,
                workspace_id=workspace_id,
            )
            counters = store.get_counters(organization_id)
            # simple linear forecast from completed jobs
            completed = float(overview["aiJobsCompleted"])
            growth = completed * 0.15
            forecast = ForecastRecord(
                id=new_id("fcst_"),
                organization_id=organization_id,
                workspace_id=workspace_id,
                metric_key="ai_jobs_completed",
                horizon_days=30,
                predicted_value=round(completed + growth, 2),
                confidence=0.72 if completed > 0 else 0.4,
                method="linear",
                metadata={"baseline": completed, "growthRate": 0.15},
            )
            store.save_forecast(forecast)
            storage_forecast = ForecastRecord(
                id=new_id("fcst_"),
                organization_id=organization_id,
                workspace_id=workspace_id,
                metric_key="storage_bytes",
                horizon_days=30,
                predicted_value=round(overview["storageUsageBytes"] * 1.2, 2),
                confidence=0.68,
                method="linear",
            )
            store.save_forecast(storage_forecast)
            return {
                "ok": True,
                "kpiDashboard": kpi["kpis"],
                "trendAnalysis": {
                    "aiJobs": overview["aiJobsCompleted"],
                    "direction": "up" if overview["aiJobsCompleted"] > 0 else "stable",
                    "apiUsage": overview["apiUsage"],
                },
                "growthAnalysis": {
                    "activeUsers": overview["activeUsers"],
                    "activeProjects": overview["activeProjects"],
                    "projectedAiJobs30d": forecast.predicted_value,
                },
                "resourceUtilization": {
                    "storageBytes": overview["storageUsageBytes"],
                    "assetUsage": overview["assetUsage"],
                    "queue": overview["queuePerformance"],
                },
                "providerPerformance": overview["providerUsage"],
                "costAnalysis": {
                    "estimatedUnits": overview["aiJobsCompleted"] * 1.0,
                    "providerMix": overview["providerUsage"],
                    "storageGb": round(overview["storageUsageBytes"] / (1024**3), 4),
                },
                "productivityAnalysis": {
                    "jobsPerUser": round(
                        overview["aiJobsCompleted"] / max(overview["activeUsers"], 1), 2
                    ),
                    "avgGenerationMs": overview["averageGenerationTimeMs"],
                    "exports": overview["exportStatistics"],
                },
                "usageForecasting": [forecast.to_dict(), storage_forecast.to_dict()],
                "countersSample": {
                    k: counters[k] for k in list(counters.keys())[:20]
                },
            }


class ReportingEngine:
    def __init__(self) -> None:
        self.analytics = AnalyticsEngine()
        self.bi = BusinessIntelligenceEngine()

    def list(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        _require_analytics(actor_id=actor_id, organization_id=organization_id)
        items = store.list_reports(organization_id)
        return {
            "ok": True,
            "count": len(items),
            "reportTypes": list(REPORT_TYPES),
            "reports": [r.to_dict() for r in items],
        }

    def generate(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op("report"):
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            workspace_id = payload.get("workspaceId") or payload.get("workspace_id")
            _require_report_write(
                actor_id=actor_id, organization_id=org_id, workspace_id=workspace_id
            )
            try:
                report_type = normalize_report_type(str(payload.get("reportType") or payload.get("type") or "daily"))
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc
            scope = str(payload.get("scope") or "organization").lower()
            start = _now()
            overview = self.analytics.overview(
                actor_id=actor_id, organization_id=org_id, workspace_id=workspace_id
            )
            bi = self.bi.insights(
                actor_id=actor_id, organization_id=org_id, workspace_id=workspace_id
            )
            period_days = {"daily": 1, "weekly": 7, "monthly": 30}.get(report_type, 7)
            period_end = _now()
            period_start = period_end - timedelta(days=period_days)
            payload_data: dict[str, Any] = {
                "overview": overview["overview"],
                "insights": {
                    "trendAnalysis": bi["trendAnalysis"],
                    "growthAnalysis": bi["growthAnalysis"],
                    "costAnalysis": bi["costAnalysis"],
                    "productivityAnalysis": bi["productivityAnalysis"],
                    "usageForecasting": bi["usageForecasting"],
                },
            }
            if report_type == "ai_usage":
                payload_data["ai"] = self.analytics.ai(
                    actor_id=actor_id, organization_id=org_id, workspace_id=workspace_id
                )
            if report_type == "storage":
                payload_data["storage"] = self.analytics.storage(
                    actor_id=actor_id, organization_id=org_id, workspace_id=workspace_id
                )
            if report_type == "performance":
                payload_data["performance"] = [p.to_dict() for p in store.list_perf(org_id)]
            if report_type in {"workspace", "team", "user", "organization"}:
                payload_data["scopeDetail"] = {
                    "scope": report_type,
                    "teams": overview["overview"]["totalTeams"],
                    "users": overview["overview"]["totalUsers"],
                }
            duration = ( _now() - start).total_seconds() * 1000
            report = ReportHistory(
                id=new_id("rpt_"),
                organization_id=org_id,
                workspace_id=str(workspace_id) if workspace_id else None,
                generated_by_id=actor_id,
                report_type=report_type,
                scope=scope,
                title=payload.get("title") or f"{report_type.replace('_', ' ').title()} Report",
                period_start=period_start,
                period_end=period_end,
                status="ready",
                payload=payload_data,
                duration_ms=round(duration, 2),
            )
            store.save_report(report)
            _audit("report.generated", actor_id, report.id, reportType=report_type)
            return {"ok": True, "report": report.to_dict()}


class AnalyticsBiService:
    def __init__(self) -> None:
        self.reporting = ReportingEngine()
        self.analytics = AnalyticsEngine()
        self.bi = BusinessIntelligenceEngine()
        self.dashboard = DashboardDataEngine()
        self.metrics = MetricsEngine()
        self.kpis = KpiEngine()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "modules": [
                "reporting_engine",
                "analytics_engine",
                "business_intelligence_engine",
                "dashboard_data_engine",
                "metrics_engine",
                "kpi_engine",
            ],
            "reportTypes": list(REPORT_TYPES),
            "kpiDefs": KPI_DEFS,
            "stats": store.metrics(),
            "engines": {
                "reporting": "ready",
                "analytics": "ready",
                "bi": "ready",
                "dashboard": "ready",
                "metrics": "ready",
                "kpi": "ready",
            },
        }

    def observability(self) -> dict[str, Any]:
        m = store.metrics()
        return {
            "ok": True,
            "apiPerformance": {
                "calls": m["apiCalls"],
                "avgLatencyMs": m["avgLatencyMs"],
            },
            "analyticsAccuracy": 1.0 - m["errorRate"],
            "reportGenerationTimeMs": m["reportAvgMs"],
            "queryPerformanceMs": m["queryAvgMs"],
            "cacheEfficiency": m["cacheHitRate"],
            "errorRate": m["errorRate"],
            "errors": m["errors"],
        }


_service: AnalyticsBiService | None = None


def get_analytics_bi_service() -> AnalyticsBiService:
    global _service
    if _service is None:
        _service = AnalyticsBiService()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    from app.services.multi_tenant.engine import reset_engine as reset_mt
    from app.services.enterprise_auth.engine import reset_engine as reset_ea

    reset_mt()
    reset_ea()
    _service = None


get_engine = get_analytics_bi_service

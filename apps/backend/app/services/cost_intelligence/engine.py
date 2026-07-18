"""Cost Intelligence Engine — facade for analytics, cost, ranking, usage, optimize."""

from __future__ import annotations

from typing import Any

from app.services.cost_intelligence import (
    analytics,
    budget,
    credit_tracker,
    monitoring,
    optimizer,
    ranking,
    reports,
    store,
    token_tracker,
)
from app.services.cost_intelligence.models import (
    OptimizeMode,
    UsageEvent,
    UsageKind,
    new_id,
)
from app.services.cost_intelligence.pricing import calculate_cost
from app.services.cost_intelligence.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION


class CostIntelligenceEngine:
    def __init__(self) -> None:
        analytics.ensure_provider_totals()
        budget.ensure_default_budget()

    def record_usage(
        self,
        provider: str,
        *,
        kind: UsageKind = "request",
        quantity: float = 1.0,
        tokens: int = 0,
        images: int = 0,
        videos: int = 0,
        audio: int = 0,
        voice: int = 0,
        storage_mb: float = 0.0,
        gpu_time_sec: float = 0.0,
        latency_ms: float = 0.0,
        success: bool = True,
        project_id: str | None = None,
        team_id: str | None = None,
        model: str | None = None,
        cost_usd: float | None = None,
    ) -> dict[str, Any]:
        provider_key = (provider or "openai").lower()
        img_n = int(images)
        vid_n = int(videos)
        aud_n = int(audio)
        voi_n = int(voice)
        tok_n = int(tokens)
        video_sec = 0.0
        audio_sec = 0.0
        voice_sec = 0.0

        if kind == "tokens" and quantity and not tok_n:
            tok_n = int(quantity)
        elif kind == "images" and quantity and not img_n:
            img_n = int(quantity)
        elif kind == "videos":
            video_sec = float(quantity) if quantity else float(vid_n)
            vid_n = max(vid_n, 1 if video_sec > 0 else 0)
        elif kind == "audio":
            audio_sec = float(quantity) if quantity else float(aud_n)
            aud_n = max(aud_n, 1 if audio_sec > 0 else 0)
        elif kind == "voice":
            voice_sec = float(quantity) if quantity else float(voi_n)
            voi_n = max(voi_n, 1 if voice_sec > 0 else 0)

        breakdown = calculate_cost(
            provider_key,
            tokens=tok_n,
            images=img_n,
            video_sec=video_sec,
            audio_sec=audio_sec,
            voice_sec=voice_sec,
            storage_mb=storage_mb,
            gpu_sec=gpu_time_sec,
            requests=1,
        )
        tokens = tok_n
        images = img_n
        videos = vid_n
        audio = aud_n
        voice = voi_n

        final_cost = float(cost_usd) if cost_usd is not None else breakdown.total_usd
        credits = breakdown.credits if cost_usd is None else final_cost / 0.01

        event = UsageEvent(
            event_id=new_id("usage"),
            provider=provider_key,
            kind=kind,
            quantity=float(quantity),
            cost_usd=final_cost,
            credits=credits,
            tokens=tokens,
            latency_ms=latency_ms,
            success=success,
            project_id=project_id,
            team_id=team_id,
            model=model,
        )
        store.save_event(event)
        token_tracker.record(provider_key, tokens)
        credit_tracker.record(
            provider_key, credits, project_id=project_id, team_id=team_id
        )
        analytics.apply_event_to_totals(
            provider_key,
            tokens=tokens,
            images=images,
            videos=int(videos) if videos else 0,
            audio=int(audio) if audio else 0,
            voice=int(voice) if voice else 0,
            storage_mb=storage_mb,
            gpu_time_sec=gpu_time_sec,
            cost_usd=final_cost,
            credits=credits,
            latency_ms=latency_ms,
            success=success,
        )
        budget.apply_spend(final_cost, project_id=project_id, team_id=team_id)
        return event.to_dict()

    def analytics(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            **analytics.provider_analytics(),
            "performance": monitoring.performance_metrics(),
        }

    def cost_summary(self) -> dict[str, Any]:
        data = analytics.provider_analytics()
        budgets = budget.list_budgets()
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "total_processing_cost": data["aggregate"]["processing_cost"],
            "avg_cost_per_request": data["aggregate"]["avg_cost_per_request"],
            "by_provider": [
                {
                    "provider": r["provider"],
                    "processing_cost": r["processing_cost"],
                    "cost_per_request": r["cost_per_request"],
                    "requests": r["requests"],
                }
                for r in data["providers"]
            ],
            "budgets": budgets,
            "daily_report": reports.daily_report(),
            "monthly_report": reports.monthly_report(),
            "performance": monitoring.performance_metrics(),
        }

    def ranking(self, *, capability: str | None = None) -> dict[str, Any]:
        ranked = ranking.rank_providers(capability=capability)
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "capability": capability,
            "ranking": [r.to_dict() for r in ranked],
            "top_provider": ranked[0].provider if ranked else None,
        }

    def usage(
        self,
        *,
        project_id: str | None = None,
        team_id: str | None = None,
        period: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "tokens": token_tracker.get(),
            "credits": credit_tracker.summary(),
            "providers": [t.to_dict() for t in store.all_totals()],
            "reports": {
                "daily": reports.daily_report(),
                "monthly": reports.monthly_report(),
            },
        }
        if project_id:
            payload["project_report"] = reports.project_report(project_id)
        if team_id:
            payload["team_report"] = reports.team_report(team_id)
        if period == "daily":
            payload["selected_report"] = payload["reports"]["daily"]
        elif period == "monthly":
            payload["selected_report"] = payload["reports"]["monthly"]
        return payload

    def optimize(
        self,
        *,
        mode: OptimizeMode = "balanced",
        capability: str | None = None,
        tokens: int = 1000,
        images: int = 0,
        video_sec: float = 0.0,
        audio_sec: float = 0.0,
        voice_sec: float = 0.0,
        prefer_provider: str | None = None,
    ) -> dict[str, Any]:
        decision = optimizer.optimize(
            mode=mode,
            capability=capability,
            tokens=tokens,
            images=images,
            video_sec=video_sec,
            audio_sec=audio_sec,
            voice_sec=voice_sec,
            prefer_provider=prefer_provider,
        )
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "optimization": decision.to_dict(),
            "history": [d.to_dict() for d in store.optimization_history(limit=10)],
        }


_engine: CostIntelligenceEngine | None = None


def get_cost_engine() -> CostIntelligenceEngine:
    global _engine
    if _engine is None:
        _engine = CostIntelligenceEngine()
    return _engine


def reset_engine() -> None:
    global _engine
    store.clear()
    token_tracker.clear()
    credit_tracker.clear()
    _engine = None

"""
Central GPU-worker AI Orchestrator.

Validates → selects provider → generate → progress webhooks → deliver.
Studio never imports Fal/Replicate SDKs — only this layer does.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.schemas.generation import GenerateRequest
from app.services.ai_service import (
    GenerationJobResult,
    LiveGenerationError,
    run_generation,
)
from app.services.providers import (
    ComfyUIProvider,
    DiffusersInstantIDProvider,
    FalProvider,
    ReplicateProvider,
)
from app.services.providers.base import BaseAIProvider

logger = logging.getLogger(__name__)


def _structured(
    event: str,
    *,
    generation_id: str | None = None,
    user_id: str | None = None,
    provider: str | None = None,
    duration_seconds: int | None = None,
    credits: int | None = None,
    latency_ms: float | None = None,
    failure: str | None = None,
    **extra: Any,
) -> None:
    payload = {
        "event": event,
        "generation_id": generation_id,
        "user_id": user_id,
        "provider": provider,
        "duration_seconds": duration_seconds,
        "credits": credits,
        "latency_ms": latency_ms,
        "failure": failure,
        **extra,
    }
    line = " ".join(f"{k}={v!r}" for k, v in payload.items() if v is not None)
    if failure:
        logger.error("orchestrator %s", line)
    else:
        logger.info("orchestrator %s", line)


def get_provider_adapters() -> dict[str, BaseAIProvider]:
    return {
        "fal": FalProvider(),
        "replicate": ReplicateProvider(),
        "comfyui": ComfyUIProvider(),
        "diffusers": DiffusersInstantIDProvider(),
    }


def select_live_provider() -> BaseAIProvider | None:
    adapters = get_provider_adapters()
    for name in ("fal", "replicate", "comfyui", "diffusers"):
        provider = adapters[name]
        if provider.is_configured():
            return provider
    return None


async def orchestrate_generation(body: GenerateRequest) -> GenerationJobResult:
    """
    Production entrypoint for /api/generate.
    Wraps run_generation with structured logging and provider selection telemetry.
    """
    started = time.perf_counter()
    generation_id = body.job_id or body.pipeline_job_id
    user_id = body.user_id
    selected = select_live_provider()

    _structured(
        "start",
        generation_id=generation_id,
        user_id=user_id,
        provider=selected.name if selected else None,
        duration_seconds=body.duration_seconds,
    )

    if (
        not body.preview_only
        and not body.use_free_trial
        and selected is None
    ):
        raise LiveGenerationError(
            "No live AI provider configured. Set FAL_KEY or REPLICATE_API_TOKEN.",
            error_code="provider_not_configured",
        )

    # Real AI intelligence stack (backend only — no UI changes).
    try:
        from app.services.intelligence.pipeline import run_intelligence_pipeline

        raw_prompt = (
            (body.fields or {}).get("directionPrompt")
            or (body.fields or {}).get("mainPrompt")
            or (body.fields or {}).get("prompt")
            or ""
        )
        plan = run_intelligence_pipeline(
            raw_prompt,
            category_hint=getattr(body, "category", None),
            style_hint=getattr(body, "visual_style", None),
            duration_hint=body.duration_seconds,
        )
        enhanced = plan.enhancement.enhanced_prompt
        if enhanced and body.fields is not None:
            # Preserve original; feed enhanced text into generation compile path.
            if "mainPrompt" in body.fields or not body.fields.get("mainPrompt"):
                body.fields["mainPrompt"] = enhanced
            body.fields["rtasOriginalPrompt"] = raw_prompt
            body.fields["rtasIntelligencePlan"] = str(plan.to_dict())[:4000]
        _structured(
            "intelligence_ready",
            generation_id=generation_id,
            user_id=user_id,
            scenes=len(plan.scenes),
            shots=len(plan.shots),
            quality_passed=plan.quality.passed,
        )
    except Exception as intel_exc:
        logger.warning("Intelligence pipeline skipped: %s", intel_exc)

    try:
        result = await run_generation(body)
    except LiveGenerationError as exc:
        _structured(
            "failed",
            generation_id=generation_id,
            user_id=user_id,
            provider=selected.name if selected else None,
            failure=str(exc),
            latency_ms=(time.perf_counter() - started) * 1000,
            error_code=getattr(exc, "error_code", None),
        )
        raise

    _structured(
        "success" if not result.simulation_mode else "simulation",
        generation_id=result.job_id,
        user_id=user_id,
        provider=result.provider,
        duration_seconds=result.duration_seconds,
        credits=result.credits_used,
        latency_ms=(time.perf_counter() - started) * 1000,
        simulation_mode=result.simulation_mode,
    )
    return result


async def provider_status(provider_name: str, external_job_id: str):
    adapters = get_provider_adapters()
    provider = adapters.get(provider_name)
    if not provider:
        raise LiveGenerationError(
            f"Unknown provider: {provider_name}",
            error_code="unknown_provider",
        )
    return await provider.status(external_job_id)


async def provider_cancel(provider_name: str, external_job_id: str) -> bool:
    adapters = get_provider_adapters()
    provider = adapters.get(provider_name)
    if not provider:
        return False
    return await provider.cancel(external_job_id)

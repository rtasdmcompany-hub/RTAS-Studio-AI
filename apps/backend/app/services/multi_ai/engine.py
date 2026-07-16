"""
Multi AI Video Generation Engine.

Detect → select → queue → generate → retry → failover → download → track.
Integrates with Prompt Understanding / Scene Breakdown via job fields metadata.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, TYPE_CHECKING

from app.services.multi_ai.models import GenerationFlowResult, QueueJob
from app.services.multi_ai.queue import generation_queue
from app.services.multi_ai.registry import (
    build_provider_registry,
    detect_available_providers,
    provider_compatibility_matrix,
)
from app.services.multi_ai.selector import (
    build_failover_chain,
    select_best_provider,
    selection_context_from_fields,
)
from app.services.providers.base import BaseAIProvider, ProviderResult

if TYPE_CHECKING:
    from app.services.ai_service import GenerationJobInput

logger = logging.getLogger(__name__)


class MultiAIVideoEngine:
    def __init__(self, registry: dict[str, BaseAIProvider] | None = None) -> None:
        self.registry = registry or build_provider_registry()

    def detect_available(self) -> list[str]:
        return detect_available_providers(self.registry)

    def compatibility(self) -> list[dict[str, Any]]:
        return provider_compatibility_matrix(self.registry)

    async def health_all(self) -> list[dict[str, Any]]:
        reports = []
        for name, adapter in self.registry.items():
            report = await adapter.health_check()
            reports.append(report.to_dict())
        return reports

    def select_provider(
        self,
        *,
        fields: dict[str, Any] | None = None,
        preferred: str | None = None,
        category: str | None = None,
        mood: str | None = None,
    ) -> str | None:
        ctx = selection_context_from_fields(fields)
        return select_best_provider(
            self.registry,
            available=self.detect_available(),
            category=category or ctx.get("category"),
            mood=mood or ctx.get("mood"),
            preferred=preferred or ctx.get("preferred"),
        )

    def enqueue(self, job_id: str, provider: str) -> QueueJob:
        return generation_queue.enqueue(job_id, provider)

    def progress(self, job_id: str) -> QueueJob | None:
        return generation_queue.get(job_id)

    async def generate_with_failover(
        self,
        job: GenerationJobInput,
        *,
        fields: dict[str, Any] | None = None,
        max_attempts_per_provider: int = 2,
        max_providers: int = 4,
    ) -> GenerationFlowResult:
        available = self.detect_available()
        primary = self.select_provider(fields=fields)
        chain = build_failover_chain(primary, available, max_providers=max_providers)

        queue_job = self.enqueue(job.job_id, chain[0] if chain else "none")
        failover_log: list[str] = []
        attempted: list[str] = []

        if not chain:
            generation_queue.update(
                job.job_id,
                state="failed",
                progress_percent=100,
                error="No live AI providers configured",
            )
            return GenerationFlowResult(
                success=False,
                provider="none",
                attempted_providers=[],
                queue_job=generation_queue.get(job.job_id) or queue_job,
                error="No live AI providers configured",
                failover_log=["no_providers_available"],
            )

        generation_queue.update(job.job_id, state="running", progress_percent=5)

        last_error: str | None = None
        for index, provider_name in enumerate(chain):
            adapter = self.registry.get(provider_name)
            if not adapter or not adapter.is_configured():
                failover_log.append(f"skip:{provider_name}:not_configured")
                continue

            attempted.append(provider_name)
            generation_queue.update(
                job.job_id,
                provider=provider_name,
                progress_percent=10 + index * 15,
                attempts=1,
            )
            cost = adapter.cost_estimate(job.duration_seconds).to_dict()
            eta = adapter.eta(job.duration_seconds).to_dict()
            logger.info(
                "multi_ai_try job=%s provider=%s attempt_chain=%s",
                job.job_id,
                provider_name,
                attempted,
            )

            result: ProviderResult | None = None
            for attempt in range(1, max_attempts_per_provider + 1):
                generation_queue.update(job.job_id, attempts=attempt)
                if attempt == 1:
                    result = await adapter.generate(job)
                else:
                    failover_log.append(f"retry:{provider_name}:{attempt}")
                    result = await adapter.retry(
                        job, attempt=attempt, max_attempts=max_attempts_per_provider
                    )
                if result and result.success:
                    local_path = result.local_mp4_path
                    if local_path is None and result.remote_url:
                        downloaded = await adapter.download(
                            result.remote_url,
                            Path(f"{provider_name}_{job.job_id}.mp4"),
                        )
                        local_path = downloaded
                        result.local_mp4_path = downloaded

                    generation_queue.update(
                        job.job_id,
                        state="completed",
                        progress_percent=100,
                        provider=provider_name,
                        result_url=result.remote_url,
                        error=None,
                    )
                    failover_log.append(f"success:{provider_name}")
                    return GenerationFlowResult(
                        success=True,
                        provider=provider_name,
                        attempted_providers=attempted,
                        queue_job=generation_queue.get(job.job_id) or queue_job,
                        remote_url=result.remote_url,
                        local_mp4_path=str(local_path) if local_path else None,
                        external_job_id=result.external_job_id,
                        cost_estimate=cost,
                        eta=eta,
                        failover_log=failover_log,
                        metadata=result.metadata or {},
                    )

                last_error = result.error if result else "unknown_error"
                failover_log.append(f"fail:{provider_name}:{last_error}")
                logger.warning(
                    "multi_ai_provider_failed job=%s provider=%s error=%s",
                    job.job_id,
                    provider_name,
                    last_error,
                )

            failover_log.append(f"failover_from:{provider_name}")

        generation_queue.update(
            job.job_id,
            state="failed",
            progress_percent=100,
            error=last_error or "All providers failed",
        )
        return GenerationFlowResult(
            success=False,
            provider=attempted[-1] if attempted else "none",
            attempted_providers=attempted,
            queue_job=generation_queue.get(job.job_id) or queue_job,
            error=last_error or "All providers failed",
            failover_log=failover_log,
        )


def get_multi_ai_engine() -> MultiAIVideoEngine:
    return MultiAIVideoEngine()

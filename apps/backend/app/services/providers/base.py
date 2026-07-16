from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from app.services.providers.contracts import (
    CostEstimate,
    ETAEstimate,
    HealthReport,
    ProviderCapability,
    RetryPlan,
)

if TYPE_CHECKING:
    from app.services.ai_service import GenerationJobInput

ProviderJobStatus = Literal[
    "queued",
    "preparing",
    "generating",
    "rendering",
    "uploading",
    "completed",
    "failed",
    "cancelled",
]


@dataclass
class ProviderResult:
    provider: str
    success: bool
    local_mp4_path: Path | None = None
    remote_url: str | None = None
    external_job_id: str | None = None
    error: str | None = None
    metadata: dict | None = None


@dataclass
class ProviderStatus:
    provider: str
    external_job_id: str
    status: ProviderJobStatus
    progress_percent: int = 0
    error: str | None = None
    remote_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAIProvider(ABC):
    """Uniform adapter contract — no provider-specific logic in Studio pages."""

    name: str = "base"
    display_name: str = "Base"
    cost_per_second_usd: float = 0.05
    typical_eta_seconds: int = 90
    max_duration_seconds: int = 10
    strengths: tuple[str, ...] = ()

    @abstractmethod
    def is_configured(self) -> bool:
        ...

    @abstractmethod
    async def generate(self, job: GenerationJobInput) -> ProviderResult:
        ...

    async def status(self, external_job_id: str) -> ProviderStatus:
        """Poll remote provider job status. Default: unknown completed/failed."""
        return ProviderStatus(
            provider=self.name,
            external_job_id=external_job_id,
            status="generating",
            progress_percent=50,
            metadata={"note": "status polling not implemented for this provider"},
        )

    async def cancel(self, external_job_id: str) -> bool:
        """Best-effort cancel. Returns True if cancel was accepted."""
        _ = external_job_id
        return False

    async def retry(
        self,
        job: GenerationJobInput,
        *,
        attempt: int = 1,
        max_attempts: int = 2,
    ) -> ProviderResult:
        """Retry generate with simple backoff metadata (no mock success)."""
        plan = RetryPlan(
            provider=self.name,
            attempt=attempt,
            max_attempts=max_attempts,
            backoff_seconds=min(8.0, 1.5 * attempt),
            reason="provider_retry",
        )
        if attempt > max_attempts:
            return ProviderResult(
                provider=self.name,
                success=False,
                error=f"{self.name}: max retries exceeded",
                metadata={"retry": plan.to_dict()},
            )
        result = await self.generate(job)
        meta = dict(result.metadata or {})
        meta["retry"] = plan.to_dict()
        result.metadata = meta
        return result

    async def download(self, remote_url: str, dest: Path) -> Path | None:
        """Download a completed remote asset to local disk."""
        if not remote_url or not remote_url.startswith("http"):
            return None
        try:
            from app.services.storage import download_mp4_to_outputs

            local_path, _public = await download_mp4_to_outputs(
                remote_url, dest.stem
            )
            return local_path
        except Exception:
            return None

    async def health_check(self) -> HealthReport:
        configured = self.is_configured()
        return HealthReport(
            provider=self.name,
            healthy=configured,
            configured=configured,
            message="configured" if configured else "missing credentials",
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    def cost_estimate(self, duration_seconds: int) -> CostEstimate:
        dur = max(1, int(duration_seconds or 1))
        return CostEstimate(
            provider=self.name,
            currency="USD",
            estimated_usd=round(self.cost_per_second_usd * dur, 4),
            cost_per_second_usd=self.cost_per_second_usd,
            duration_seconds=dur,
        )

    def eta(self, duration_seconds: int = 5) -> ETAEstimate:
        # Longer clips take longer; keep deterministic.
        extra = max(0, int(duration_seconds) - 5) * 8
        return ETAEstimate(
            provider=self.name,
            eta_seconds=int(self.typical_eta_seconds + extra),
            confidence=0.6 if self.is_configured() else 0.2,
        )

    def capability(self) -> ProviderCapability:
        return ProviderCapability(
            provider=self.name,
            display_name=self.display_name,
            strengths=list(self.strengths),
            max_duration_seconds=self.max_duration_seconds,
            fal_model=getattr(self, "fal_model", None),
        )

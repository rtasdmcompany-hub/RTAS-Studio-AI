from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

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

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.ai_service import GenerationJobInput


@dataclass
class ProviderResult:
    provider: str
    success: bool
    local_mp4_path: Path | None = None
    remote_url: str | None = None
    external_job_id: str | None = None
    error: str | None = None
    metadata: dict | None = None


class BaseAIProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(self, job: GenerationJobInput) -> ProviderResult:
        ...

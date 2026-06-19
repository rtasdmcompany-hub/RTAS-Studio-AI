"""
Local Diffusers + InstantID worker (GPU server scaffold).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.config import settings
from app.services.providers.base import BaseAIProvider, ProviderResult

if TYPE_CHECKING:
    from app.services.ai_service import GenerationJobInput

logger = logging.getLogger(__name__)


class DiffusersInstantIDProvider(BaseAIProvider):
    name = "diffusers"

    def is_configured(self) -> bool:
        return settings.diffusers_enabled

    async def generate(self, job: GenerationJobInput) -> ProviderResult:
        if not self.is_configured():
            return ProviderResult(
                provider=self.name,
                success=False,
                error="DIFFUSERS_ENABLED=false — enable when GPU worker is ready",
            )

        if not job.face_reference_path and job.visual_style == "real":
            return ProviderResult(
                provider=self.name,
                success=False,
                error="face_reference image required for InstantID",
            )

        # TODO: torch + diffusers pipeline
        # - load InstantID / IP-Adapter weights from instantid_model_path
        # - condition on job.face_reference_path
        # - export frames → ffmpeg → job.output_path
        logger.info(
            "Diffusers scaffold: job=%s device=%s strength=%s",
            job.job_id,
            settings.diffusers_device,
            job.identity_strength,
        )

        return ProviderResult(
            provider=self.name,
            success=False,
            error="Local Diffusers worker pending",
            metadata={"device": settings.diffusers_device},
        )

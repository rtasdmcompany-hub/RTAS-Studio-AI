"""
ComfyUI API — workflow queue (production scaffold).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.config import settings
from app.services.providers.base import BaseAIProvider, ProviderResult

if TYPE_CHECKING:
    from app.services.ai_service import GenerationJobInput

logger = logging.getLogger(__name__)


class ComfyUIProvider(BaseAIProvider):
    name = "comfyui"

    def is_configured(self) -> bool:
        return bool(settings.comfyui_api_url)

    async def generate(self, job: GenerationJobInput) -> ProviderResult:
        if not self.is_configured():
            return ProviderResult(
                provider=self.name,
                success=False,
                error="COMFYUI_API_URL not configured",
            )

        # TODO: POST {comfyui_api_url}/prompt with workflow JSON
        # workflow = build_comfy_workflow(job)  # InstantID + AnimateDiff etc.
        logger.info(
            "ComfyUI scaffold: job=%s url=%s",
            job.job_id,
            settings.comfyui_api_url,
        )

        return ProviderResult(
            provider=self.name,
            success=False,
            error="ComfyUI workflow runner pending",
            metadata={"workflow": "rtas_instantid_v1_placeholder"},
        )

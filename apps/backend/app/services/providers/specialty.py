"""
Specialty video adapters (Veo, Runway, Kling, Hailuo, Pika, Luma, SVD, CogVideo).

Each adapter implements the full Multi-AI contract. Live generation uses:
1) Native API key when present (HTTP), or
2) Fal gateway model when FAL_KEY is present.

No mock success paths — unconfigured providers return hard failures.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.core.config import reload_settings, settings
from app.services.providers.base import BaseAIProvider, ProviderResult
from app.services.providers.fal_gateway import (
    fal_key_available,
    fal_status_stub,
    fal_subscribe_generate,
)

if TYPE_CHECKING:
    from app.services.ai_service import GenerationJobInput

logger = logging.getLogger(__name__)


class SpecialtyVideoProvider(BaseAIProvider):
    """Base for Fal-or-native specialty video models."""

    fal_model: str = ""
    native_env_attr: str = ""
    native_base_url: str = ""

    def _native_key(self) -> str | None:
        reload_settings()
        if not self.native_env_attr:
            return None
        val = getattr(settings, self.native_env_attr, None)
        if isinstance(val, str) and val.strip():
            return val.strip()
        return None

    def is_configured(self) -> bool:
        return bool(self._native_key() or (fal_key_available() and self.fal_model))

    async def generate(self, job: GenerationJobInput) -> ProviderResult:
        if not self.is_configured():
            return ProviderResult(
                provider=self.name,
                success=False,
                error=f"{self.display_name} not configured (set native key or FAL_KEY)",
                metadata={"error_code": "provider_not_configured"},
            )

        # Prefer Fal gateway when available (production-proven path in this stack).
        if fal_key_available() and self.fal_model:
            return await fal_subscribe_generate(
                provider_name=self.name,
                model_id=self.fal_model,
                job=job,
            )

        # Native REST — implemented when key present without Fal.
        return await self._generate_native(job)

    async def _generate_native(self, job: GenerationJobInput) -> ProviderResult:
        key = self._native_key()
        if not key or not self.native_base_url:
            return ProviderResult(
                provider=self.name,
                success=False,
                error=f"{self.display_name}: native endpoint not available",
                metadata={"error_code": "provider_not_configured"},
            )
        # Real HTTP attempt — fail clearly if API rejects (no fake MP4).
        try:
            import httpx
        except ImportError as exc:
            return ProviderResult(
                provider=self.name,
                success=False,
                error=f"httpx missing: {exc}",
                metadata={"error_code": "dependency_missing"},
            )

        prompt = (job.compiled_prompt or job.main_prompt or "").strip()
        payload: dict[str, Any] = {
            "prompt": prompt,
            "duration": int(job.duration_seconds or 5),
        }
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    self.native_base_url, json=payload, headers=headers
                )
        except Exception as exc:
            return ProviderResult(
                provider=self.name,
                success=False,
                error=str(exc),
                metadata={"error_code": "provider_generate_failed"},
            )

        if resp.status_code >= 400:
            return ProviderResult(
                provider=self.name,
                success=False,
                error=f"{self.display_name} HTTP {resp.status_code}: {resp.text[:300]}",
                metadata={"error_code": "provider_http_error", "status_code": resp.status_code},
            )

        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        remote = None
        if isinstance(data, dict):
            remote = (
                data.get("video_url")
                or data.get("url")
                or (data.get("output") if isinstance(data.get("output"), str) else None)
            )
            if isinstance(data.get("data"), dict):
                remote = remote or data["data"].get("video_url") or data["data"].get("url")

        if not isinstance(remote, str) or not remote.startswith("http"):
            return ProviderResult(
                provider=self.name,
                success=False,
                error=f"{self.display_name}: response missing video URL",
                metadata={"error_code": "empty_output"},
            )

        local = await self.download(remote, Path(f"{self.name}_{job.job_id}.mp4"))
        return ProviderResult(
            provider=self.name,
            success=True,
            remote_url=remote,
            local_mp4_path=local,
            external_job_id=str(data.get("id") or data.get("job_id") or job.job_id),
            metadata={"gateway": "native"},
        )

    async def status(self, external_job_id: str):
        return await fal_status_stub(self.name, external_job_id)


class GoogleVeoProvider(SpecialtyVideoProvider):
    name = "veo"
    display_name = "Google Veo"
    fal_model = "fal-ai/veo2"
    native_env_attr = "google_veo_api_key"
    cost_per_second_usd = 0.12
    typical_eta_seconds = 120
    max_duration_seconds = 8
    strengths = ("cinematic", "photoreal", "movie_scene")


class RunwayProvider(SpecialtyVideoProvider):
    name = "runway"
    display_name = "Runway"
    fal_model = "fal-ai/runway-gen3/turbo/image-to-video"
    native_env_attr = "runway_api_key"
    native_base_url = "https://api.dev.runwayml.com/v1/image_to_video"
    cost_per_second_usd = 0.10
    typical_eta_seconds = 100
    max_duration_seconds = 10
    strengths = ("commercial", "product", "motion_graphics")


class KlingProvider(SpecialtyVideoProvider):
    name = "kling"
    display_name = "Kling AI"
    fal_model = "fal-ai/kling-video/v1.6/standard/image-to-video"
    native_env_attr = "kling_api_key"
    cost_per_second_usd = 0.08
    typical_eta_seconds = 110
    max_duration_seconds = 10
    strengths = ("cinematic", "character", "narrative")


class HailuoProvider(SpecialtyVideoProvider):
    name = "hailuo"
    display_name = "Hailuo AI"
    fal_model = "fal-ai/minimax/video-01"
    native_env_attr = "hailuo_api_key"
    cost_per_second_usd = 0.07
    typical_eta_seconds = 95
    max_duration_seconds = 6
    strengths = ("story", "emotion", "short_film")


class PikaProvider(SpecialtyVideoProvider):
    name = "pika"
    display_name = "Pika"
    fal_model = "fal-ai/pika/v2/turbo/text-to-video"
    native_env_attr = "pika_api_key"
    cost_per_second_usd = 0.06
    typical_eta_seconds = 80
    max_duration_seconds = 5
    strengths = ("social", "tiktok", "reel", "music_video")


class LumaProvider(SpecialtyVideoProvider):
    name = "luma"
    display_name = "Luma Dream Machine"
    fal_model = "fal-ai/luma-dream-machine"
    native_env_attr = "luma_api_key"
    cost_per_second_usd = 0.09
    typical_eta_seconds = 100
    max_duration_seconds = 5
    strengths = ("cinematic", "trailer", "dreamy")


class StableVideoDiffusionProvider(SpecialtyVideoProvider):
    name = "svd"
    display_name = "Stable Video Diffusion"
    fal_model = "fal-ai/stable-video"
    native_env_attr = "svd_api_key"
    cost_per_second_usd = 0.04
    typical_eta_seconds = 70
    max_duration_seconds = 4
    strengths = ("i2v", "economy", "product")


class CogVideoProvider(SpecialtyVideoProvider):
    name = "cogvideo"
    display_name = "CogVideo"
    fal_model = "fal-ai/cogvideox-5b"
    native_env_attr = "cogvideo_api_key"
    cost_per_second_usd = 0.05
    typical_eta_seconds = 130
    max_duration_seconds = 6
    strengths = ("t2v", "research", "narrative")

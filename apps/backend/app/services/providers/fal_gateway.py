"""Shared Fal.ai gateway used by specialty video adapters (no mock paths)."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, TYPE_CHECKING

from app.core.config import reload_settings, settings
from app.services.providers.base import ProviderResult, ProviderStatus

if TYPE_CHECKING:
    from app.services.ai_service import GenerationJobInput

logger = logging.getLogger(__name__)


def fal_key_available() -> bool:
    reload_settings()
    return bool(settings.fal_key and str(settings.fal_key).strip())


def apply_fal_key() -> str:
    fresh = reload_settings()
    key = str(fresh.fal_key or "").strip()
    if key:
        os.environ["FAL_KEY"] = key
    return key


def _extract_video_url(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    for key in ("video", "video_url", "url", "output"):
        val = payload.get(key)
        if isinstance(val, str) and val.startswith("http"):
            return val
        if isinstance(val, dict):
            nested = val.get("url") or val.get("video") or val.get("video_url")
            if isinstance(nested, str) and nested.startswith("http"):
                return nested
    videos = payload.get("videos")
    if isinstance(videos, list) and videos:
        first = videos[0]
        if isinstance(first, str) and first.startswith("http"):
            return first
        if isinstance(first, dict):
            u = first.get("url")
            if isinstance(u, str) and u.startswith("http"):
                return u
    return None


async def fal_subscribe_generate(
    *,
    provider_name: str,
    model_id: str,
    job: GenerationJobInput,
    extra_arguments: dict[str, Any] | None = None,
) -> ProviderResult:
    """Run a Fal model subscribe call for a specialty adapter."""
    if not fal_key_available():
        return ProviderResult(
            provider=provider_name,
            success=False,
            error=f"{provider_name}: FAL_KEY not configured",
            metadata={"error_code": "provider_not_configured"},
        )

    apply_fal_key()
    try:
        import fal_client
    except ImportError as exc:
        return ProviderResult(
            provider=provider_name,
            success=False,
            error=f"fal-client not installed: {exc}",
            metadata={"error_code": "dependency_missing"},
        )

    prompt = (job.compiled_prompt or job.main_prompt or "").strip()
    duration = max(2, min(int(job.duration_seconds or 5), 15))
    arguments: dict[str, Any] = {
        "prompt": prompt,
        "duration": duration,
    }
    # Image-to-video when a reference exists.
    image_url = None
    for attr in ("source_image_url", "face_reference_url", "image_url"):
        val = getattr(job, attr, None)
        if isinstance(val, str) and val.startswith("http"):
            image_url = val
            break
    if image_url:
        arguments["image_url"] = image_url
    if extra_arguments:
        arguments.update(extra_arguments)

    logger.info(
        "multi_ai fal_gateway provider=%s model=%s duration=%s",
        provider_name,
        model_id,
        duration,
    )

    try:
        result = await asyncio.to_thread(
            fal_client.subscribe,
            model_id,
            arguments=arguments,
        )
    except Exception as exc:
        logger.exception("fal_gateway failed provider=%s", provider_name)
        return ProviderResult(
            provider=provider_name,
            success=False,
            error=str(exc),
            metadata={"error_code": "provider_generate_failed", "model_id": model_id},
        )

    remote = _extract_video_url(result)
    if not remote:
        return ProviderResult(
            provider=provider_name,
            success=False,
            error="Fal returned no video URL",
            metadata={"error_code": "empty_output", "raw_keys": list(result.keys()) if isinstance(result, dict) else []},
        )

    local_path: Path | None = None
    try:
        from app.services.storage import download_mp4_to_outputs

        local_path, _ = await download_mp4_to_outputs(remote, f"{provider_name}_{job.job_id}")
    except Exception as dl_exc:
        logger.warning("download after fal generate failed: %s", dl_exc)

    return ProviderResult(
        provider=provider_name,
        success=True,
        local_mp4_path=local_path,
        remote_url=remote,
        external_job_id=str(
            (result.get("request_id") if isinstance(result, dict) else None)
            or f"{provider_name}:{job.job_id}"
        ),
        metadata={"model_id": model_id, "gateway": "fal"},
    )


async def fal_status_stub(provider_name: str, external_job_id: str) -> ProviderStatus:
    return ProviderStatus(
        provider=provider_name,
        external_job_id=external_job_id,
        status="generating",
        progress_percent=50,
        metadata={"note": "poll via fal gateway generate path"},
    )

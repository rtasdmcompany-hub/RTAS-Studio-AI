"""
Batch Fal.ai 15-second clips and stitch into one full-length music video.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx

from app.core.config import reload_settings, settings
from app.services.fal_guard import (
    assert_fal_live_allowed,
    classify_and_record_fal_failure,
    record_fal_success,
)
from app.core.errors import is_fal_auth_failure, is_fal_credit_failure
from app.services.providers.fal import (
    FAL_CLIP_MAX_SECONDS,
    FAL_CLIP_MIN_SECONDS,
    _build_fal_request,
    _build_video_prompt,
    _duration_for_fal,
    _exception_details,
    _extract_video_url,
    _run_fal_subscribe_sync,
    _sanitize_fal_arguments,
)
from app.services.providers.base import ProviderResult
from app.services.storage import job_output_path
from app.services.video_stitch import VideoStitchError, stitch_clips_with_audio

if TYPE_CHECKING:
    from app.services.ai_service import GenerationJobInput

logger = logging.getLogger(__name__)


def plan_clip_durations(target_seconds: int) -> list[int]:
    """Split target length into Fal-legal clip durations (2–15 sec each)."""
    target = max(FAL_CLIP_MIN_SECONDS, min(int(target_seconds), 420))
    clips: list[int] = []
    remaining = target
    max_clips = 28  # 7 minutes at 15s per clip
    while remaining > 0 and len(clips) < max_clips:
        chunk = min(FAL_CLIP_MAX_SECONDS, remaining)
        chunk = max(FAL_CLIP_MIN_SECONDS, chunk)
        clips.append(chunk)
        remaining -= chunk
    return clips


def _segment_prompt(base: str, index: int, total: int) -> str:
    return (
        f"{base} Continuous music video segment {index + 1} of {total}. "
        "Same character, same face identity, same wardrobe and lighting. "
        "Smooth motion continuity for seamless edit."
    )[:2000]


async def _download_clip(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(follow_redirects=True, timeout=300.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        dest.write_bytes(response.content)


async def generate_multiclip_fal(job: GenerationJobInput) -> ProviderResult:
    """Generate many 15s Fal clips and stitch to match audio / requested duration."""
    from app.services.providers.fal import FalProvider

    reload_settings()
    provider = FalProvider()
    if not provider.is_configured():
        return ProviderResult(
            provider="fal",
            success=False,
            error="FAL_KEY not configured",
        )
    provider._apply_api_key()
    clip_durations = plan_clip_durations(job.duration_seconds)
    total = len(clip_durations)
    base_prompt = _build_video_prompt(job)

    endpoint, base_args = _build_fal_request(job)
    work_dir = settings.local_output_dir / job.job_id / "clips"
    work_dir.mkdir(parents=True, exist_ok=True)

    downloaded: list[Path] = []

    for index, clip_sec in enumerate(clip_durations):
        assert_fal_live_allowed(job.job_id)
        arguments: dict[str, Any] = dict(base_args)
        arguments["prompt"] = _segment_prompt(base_prompt, index, total)
        arguments["duration"] = _duration_for_fal(clip_sec)
        arguments = _sanitize_fal_arguments(arguments)

        logger.info(
            "Fal multiclip job=%s clip=%s/%s duration=%s",
            job.job_id,
            index + 1,
            total,
            arguments["duration"],
        )

        try:
            result = await asyncio.to_thread(
                _run_fal_subscribe_sync,
                endpoint,
                arguments,
            )
        except ValueError as exc:
            message = str(exc)
            if is_fal_credit_failure(message):
                user_msg = classify_and_record_fal_failure(message, "fal_credit")
                return ProviderResult(
                    provider="fal",
                    success=False,
                    error=user_msg,
                    metadata={"error_code": "fal_credit", "clip": index + 1},
                )
            if is_fal_auth_failure(message):
                user_msg = classify_and_record_fal_failure(message, "fal_auth")
                return ProviderResult(
                    provider="fal",
                    success=False,
                    error=user_msg,
                    metadata={"error_code": "fal_auth", "clip": index + 1},
                )
            return ProviderResult(
                provider="fal",
                success=False,
                error=message,
                metadata={"clip": index + 1},
            )
        except Exception as exc:
            message, status_code = _exception_details(exc)
            if is_fal_credit_failure(message, status_code):
                user_msg = classify_and_record_fal_failure(message, "fal_credit")
                return ProviderResult(
                    provider="fal",
                    success=False,
                    error=user_msg,
                    metadata={"error_code": "fal_credit", "clip": index + 1},
                )
            if is_fal_auth_failure(message, status_code):
                user_msg = classify_and_record_fal_failure(message, "fal_auth")
                return ProviderResult(
                    provider="fal",
                    success=False,
                    error=user_msg,
                    metadata={"error_code": "fal_auth", "clip": index + 1},
                )
            classify_and_record_fal_failure(message or str(exc))
            return ProviderResult(
                provider="fal",
                success=False,
                error=f"Fal clip {index + 1}/{total} failed: {exc}",
                metadata={"clip": index + 1},
            )

        url = _extract_video_url(result)
        if not url:
            return ProviderResult(
                provider="fal",
                success=False,
                error=f"Fal clip {index + 1}/{total} returned no video URL",
            )

        clip_path = work_dir / f"clip_{index:03d}.mp4"
        try:
            await _download_clip(url, clip_path)
        except Exception as exc:
            return ProviderResult(
                provider="fal",
                success=False,
                error=f"Failed to download Fal clip {index + 1}: {exc}",
            )
        downloaded.append(clip_path)
        record_fal_success()

    output = job_output_path(job.job_id)
    audio_path = (
        job.audio_source.local_path
        if job.audio_source and job.audio_source.exists
        else None
    )

    try:
        await asyncio.to_thread(
            stitch_clips_with_audio,
            downloaded,
            output,
            audio_path,
            float(job.duration_seconds),
        )
    except VideoStitchError as exc:
        return ProviderResult(
            provider="fal",
            success=False,
            error=str(exc),
        )

    record_fal_success()
    delivery = f"{settings.public_base_url.rstrip('/')}/media/outputs/{job.job_id}.mp4"
    return ProviderResult(
        provider="fal",
        success=True,
        local_mp4_path=output,
        remote_url=delivery,
        metadata={
            "multiclip": True,
            "clip_count": total,
            "target_duration_sec": job.duration_seconds,
            "endpoint": endpoint,
        },
    )

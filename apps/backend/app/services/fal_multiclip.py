"""
Batch Fal.ai 15-second clips and stitch into one full-length music video.
Concurrent chunk orchestration with pipeline status reporting.
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
from app.services.job_progress import PipelineProgressReporter
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

# Limit parallel Fal calls — avoids rate limits while beating serial 504 timeouts.
_MAX_CONCURRENT_CLIPS = 3


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
    from app.services.ssrf_guard import SsrfError, assert_safe_outbound_url

    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        safe_url = assert_safe_outbound_url(url)
    except SsrfError as exc:
        raise ValueError(f"Blocked unsafe clip URL: {exc}") from exc
    async with httpx.AsyncClient(follow_redirects=False, timeout=300.0) as client:
        response = await client.get(safe_url)
        response.raise_for_status()
        dest.write_bytes(response.content)


def _provider_failure(
    message: str,
    *,
    clip: int,
    error_code: str | None = None,
) -> ProviderResult:
    meta: dict[str, Any] = {"clip": clip}
    if error_code:
        meta["error_code"] = error_code
    return ProviderResult(provider="fal", success=False, error=message, metadata=meta)


async def _generate_single_clip(
    job: GenerationJobInput,
    *,
    index: int,
    clip_sec: int,
    total: int,
    base_prompt: str,
    endpoint: str,
    base_args: dict[str, Any],
    work_dir: Path,
    semaphore: asyncio.Semaphore,
    progress: PipelineProgressReporter | None,
) -> tuple[int, Path, str]:
    async with semaphore:
        if progress:
            await progress.chunk_started(index, total, clip_sec)

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
                raise RuntimeError(user_msg) from exc
            if is_fal_auth_failure(message):
                user_msg = classify_and_record_fal_failure(message, "fal_auth")
                raise RuntimeError(user_msg) from exc
            raise RuntimeError(message) from exc
        except Exception as exc:
            message, status_code = _exception_details(exc)
            if is_fal_credit_failure(message, status_code):
                user_msg = classify_and_record_fal_failure(message, "fal_credit")
                raise RuntimeError(user_msg) from exc
            if is_fal_auth_failure(message, status_code):
                user_msg = classify_and_record_fal_failure(message, "fal_auth")
                raise RuntimeError(user_msg) from exc
            classify_and_record_fal_failure(message or str(exc))
            raise RuntimeError(f"Fal clip {index + 1}/{total} failed: {exc}") from exc

        url = _extract_video_url(result)
        if not url:
            raise RuntimeError(f"Fal clip {index + 1}/{total} returned no video URL")

        clip_path = work_dir / f"clip_{index:03d}.mp4"
        try:
            await _download_clip(url, clip_path)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to download Fal clip {index + 1}: {exc}"
            ) from exc

        if not clip_path.is_file() or clip_path.stat().st_size < 1024:
            raise RuntimeError(f"Fal clip {index + 1}/{total} download was empty")

        record_fal_success()
        if progress:
            await progress.chunk_completed(
                index,
                total,
                fal_url=url,
                local_path=str(clip_path),
            )
        return index, clip_path, url


async def generate_multiclip_fal(
    job: GenerationJobInput,
    *,
    progress: PipelineProgressReporter | None = None,
) -> ProviderResult:
    """Generate many 15s Fal clips concurrently and stitch to target duration."""
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

    if progress:
        await progress.queued(total)

    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_CLIPS)
    tasks = [
        _generate_single_clip(
            job,
            index=index,
            clip_sec=clip_sec,
            total=total,
            base_prompt=base_prompt,
            endpoint=endpoint,
            base_args=base_args,
            work_dir=work_dir,
            semaphore=semaphore,
            progress=progress,
        )
        for index, clip_sec in enumerate(clip_durations)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    ordered: list[Path | None] = [None] * total
    for item in results:
        if isinstance(item, BaseException):
            message = str(item)
            if progress:
                await progress.failed(message, total)
            if is_fal_credit_failure(message):
                return _provider_failure(message, clip=0, error_code="fal_credit")
            if is_fal_auth_failure(message):
                return _provider_failure(message, clip=0, error_code="fal_auth")
            return ProviderResult(
                provider="fal",
                success=False,
                error=message,
                metadata={"multiclip": True, "clip_count": total},
            )
        index, clip_path, _url = item
        ordered[index] = clip_path

    missing = [i for i, path in enumerate(ordered) if path is None]
    if missing:
        message = f"Missing Fal clip(s) at index(es) {missing} — aborting stitch"
        if progress:
            await progress.failed(message, total)
        return ProviderResult(
            provider="fal",
            success=False,
            error=message,
            metadata={"multiclip": True, "missing_chunks": missing},
        )

    downloaded = [ordered[i] for i in range(total) if ordered[i] is not None]

    if progress:
        await progress.compiling(total)

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
        if progress:
            await progress.failed(str(exc), total)
        return ProviderResult(
            provider="fal",
            success=False,
            error=str(exc),
            metadata={"multiclip": True, "stage": "compiling_media"},
        )

    record_fal_success()
    delivery = f"{settings.public_base_url.rstrip('/')}/media/outputs/{job.job_id}.mp4"
    if progress:
        await progress.completed(delivery, total)

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

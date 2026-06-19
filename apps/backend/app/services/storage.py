"""
Local and cloud-ready storage for generated MP4 assets.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def ensure_dirs() -> None:
    settings.local_upload_dir.mkdir(parents=True, exist_ok=True)
    settings.local_output_dir.mkdir(parents=True, exist_ok=True)


def job_upload_dir(job_id: str) -> Path:
    path = settings.local_upload_dir / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_upload_path(job_id: str, field_id: str, filename: str) -> Path:
    safe_name = filename.replace("..", "").replace("/", "_")
    return job_upload_dir(job_id) / f"{field_id}_{safe_name}"


def job_output_path(job_id: str, suffix: str = ".mp4") -> Path:
    ensure_dirs()
    return settings.local_output_dir / f"{job_id}{suffix}"


def publish_local_mp4(source: Path, job_id: str) -> tuple[Path, str]:
    ensure_dirs()
    dest = job_output_path(job_id)
    if source.resolve() != dest.resolve():
        if source.exists():
            shutil.copy2(source, dest)
        elif not dest.exists():
            raise FileNotFoundError(f"Output MP4 missing: {source}")

    delivery_url = f"{settings.public_base_url.rstrip('/')}/media/outputs/{job_id}.mp4"
    return dest, delivery_url


async def download_mp4_to_outputs(remote_url: str, job_id: str) -> tuple[Path, str]:
    """Download Replicate CDN MP4 into local outputs for stable playback."""
    dest = job_output_path(job_id)
    ensure_dirs()

    async with httpx.AsyncClient(follow_redirects=True, timeout=300.0) as client:
        response = await client.get(remote_url)
        response.raise_for_status()
        dest.write_bytes(response.content)

    delivery_url = f"{settings.public_base_url.rstrip('/')}/media/outputs/{job_id}.mp4"
    logger.info("Cached remote MP4 job=%s path=%s", job_id, dest)
    return dest, delivery_url


async def publish_from_url(remote_url: str, job_id: str) -> tuple[Path, str]:
    """
    Cache provider MP4 locally when enabled; otherwise return remote URL as delivery.
    """
    if settings.replicate_cache_outputs_locally and remote_url.startswith("http"):
        try:
            return await download_mp4_to_outputs(remote_url, job_id)
        except Exception as exc:
            logger.warning("MP4 cache failed, using remote URL: %s", exc)

    dest = job_output_path(job_id)
    return dest, remote_url

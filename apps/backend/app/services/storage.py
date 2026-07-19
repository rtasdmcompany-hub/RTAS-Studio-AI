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
    """Create local media dirs; fall back to /tmp on read-only serverless runtimes."""
    import tempfile

    for attr in ("local_upload_dir", "local_output_dir"):
        path: Path = getattr(settings, attr)
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError:
            fallback = Path(tempfile.gettempdir()) / "rtas" / path.name
            try:
                fallback.mkdir(parents=True, exist_ok=True)
            except OSError:
                logger.warning("Unable to create media dir for %s", attr)
                continue
            try:
                setattr(settings, attr, fallback)
            except Exception:
                settings.__dict__[attr] = fallback
            logger.warning(
                "Using temp media dir for %s -> %s (read-only runtime)",
                attr,
                fallback,
            )



def job_upload_dir(job_id: str) -> Path:
    safe = job_id.replace("..", "").replace("/", "_").replace("\\", "_")
    path = settings.local_upload_dir / safe
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_upload_path(job_id: str, field_id: str, filename: str) -> Path:
    safe_name = Path(filename).name.replace("..", "").replace("/", "_").replace("\\", "_")
    return job_upload_dir(job_id) / f"{field_id}_{safe_name}"


def job_output_path(job_id: str, suffix: str = ".mp4") -> Path:
    ensure_dirs()
    safe = job_id.replace("..", "").replace("/", "_").replace("\\", "_")
    return settings.local_output_dir / f"{safe}{suffix}"


def publish_local_mp4(source: Path, job_id: str) -> tuple[Path, str]:
    ensure_dirs()
    dest = job_output_path(job_id)
    if source.resolve() != dest.resolve():
        if source.exists():
            shutil.copy2(source, dest)
        elif not dest.exists():
            raise FileNotFoundError(f"Output MP4 missing: {source}")

    delivery_url = f"{settings.public_base_url.rstrip('/')}/media/outputs/{Path(dest).name}"
    return dest, delivery_url


async def download_mp4_to_outputs(remote_url: str, job_id: str) -> tuple[Path, str]:
    """Download provider CDN MP4 into local outputs for stable playback."""
    from app.core.runtime import is_production
    from app.services.ssrf_guard import SsrfError, assert_safe_outbound_url

    try:
        safe_url = assert_safe_outbound_url(remote_url)
    except SsrfError as exc:
        raise ValueError(f"Blocked unsafe outbound media URL: {exc}") from exc

    dest = job_output_path(job_id)
    ensure_dirs()

    # Do not follow redirects — prevents redirect-to-internal SSRF after allowlist check.
    async with httpx.AsyncClient(follow_redirects=False, timeout=300.0) as client:
        response = await client.get(safe_url)
        response.raise_for_status()
        dest.write_bytes(response.content)

    if is_production():
        # Public /media/outputs mount is disabled in production — return provider URL.
        delivery_url = safe_url
    else:
        delivery_url = f"{settings.public_base_url.rstrip('/')}/media/outputs/{Path(dest).name}"
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

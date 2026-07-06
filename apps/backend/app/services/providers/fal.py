"""
Fal.ai cloud GPU — Wan 2.7 I2V / T2V via official fal-client SDK.

Models (override via .env):
  - fal-ai/wan/v2.7/image-to-video
  - fal-ai/wan/v2.7/text-to-video
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, TYPE_CHECKING
from urllib.parse import urlparse

import fal_client

from app.core.config import BackendRoot, reload_settings, settings
from app.core.errors import (
    FAL_AUTH_USER_MESSAGE,
    FAL_CREDIT_USER_MESSAGE,
    is_fal_auth_failure,
    is_fal_credit_failure,
)
from app.services.fal_guard import (
    assert_fal_live_allowed,
    classify_and_record_fal_failure,
    record_fal_success,
)
from app.services.providers.base import BaseAIProvider, ProviderResult

if TYPE_CHECKING:
    from app.services.ai_service import GenerationJobInput

logger = logging.getLogger(__name__)

_MIN_DURATION = 2
_MAX_DURATION = 15
FAL_CLIP_MIN_SECONDS = _MIN_DURATION
FAL_CLIP_MAX_SECONDS = _MAX_DURATION
_UPLOAD_CACHE_PATH = BackendRoot / "data" / "fal-upload-cache.json"


def _sanitize_fal_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    """Fal Wan 2.7 requires duration as int 2–15 — never string/empty."""
    out = dict(arguments)
    raw = out.get("duration")
    try:
        if raw is None or raw == "":
            parsed = _MAX_DURATION
        else:
            parsed = int(float(str(raw).strip()))
    except (TypeError, ValueError):
        parsed = _MAX_DURATION
    out["duration"] = max(_MIN_DURATION, min(_MAX_DURATION, parsed))
    return out


def _exception_details(exc: BaseException) -> tuple[str, int | None]:
    """Collect message and HTTP status from Fal/httpx exception chains."""
    message = str(exc)
    status_code: int | None = None
    for node in (exc, exc.__cause__, exc.__context__):
        if node is None:
            continue
        if status_code is None:
            raw = getattr(node, "status_code", None) or getattr(node, "status", None)
            if isinstance(raw, int):
                status_code = raw
        response = getattr(node, "response", None)
        if response is not None and status_code is None:
            raw = getattr(response, "status_code", None)
            if isinstance(raw, int):
                status_code = raw
    return message, status_code


class FalProvider(BaseAIProvider):
    name = "fal"

    def is_configured(self) -> bool:
        return settings.fal_configured

    def _apply_api_key(self) -> str:
        fresh = reload_settings()
        key = str(fresh.fal_key or "").strip()
        if key:
            os.environ["FAL_KEY"] = key
        return key

    async def generate(self, job: GenerationJobInput) -> ProviderResult:
        if not self.is_configured():
            return ProviderResult(
                provider=self.name,
                success=False,
                error="FAL_KEY not configured",
            )

        try:
            assert_fal_live_allowed(job.job_id)
            self._apply_api_key()

            target_seconds = max(_MIN_DURATION, int(job.duration_seconds))
            if target_seconds > _MAX_DURATION:
                from app.services.fal_multiclip import generate_multiclip_fal

                progress = getattr(job, "pipeline_progress", None)
                return await generate_multiclip_fal(job, progress=progress)

            endpoint, arguments = _build_fal_request(job)
            arguments = _sanitize_fal_arguments(arguments)
            logger.info(
                "Fal subscribe job=%s endpoint=%s model=%s cost=$%.3f/s has_image=%s duration=%s",
                job.job_id,
                endpoint,
                job.selected_model_id or "legacy",
                job.selected_cost_per_second or 0.0,
                "image_url" in arguments,
                arguments.get("duration"),
            )

            result = await asyncio.to_thread(
                _run_fal_subscribe_sync,
                endpoint,
                arguments,
            )
            output_url = _extract_video_url(result)
            if not output_url:
                raise ValueError(f"Fal returned no video URL. output={result!r}")

            record_fal_success()
            return ProviderResult(
                provider=self.name,
                success=True,
                remote_url=output_url,
                metadata={
                    "endpoint": endpoint,
                    "duration": arguments.get("duration"),
                    "resolution": arguments.get("resolution"),
                    "output_url": output_url,
                },
            )
        except ValueError as exc:
            message = str(exc)
            if is_fal_credit_failure(message):
                print(f"Fal API Error: {message}", flush=True)
                user_msg = classify_and_record_fal_failure(message, "fal_credit")
                return ProviderResult(
                    provider=self.name,
                    success=False,
                    error=user_msg,
                    metadata={"error_code": "fal_credit"},
                )
            if is_fal_auth_failure(message):
                print(f"Fal API Error: {message}", flush=True)
                user_msg = classify_and_record_fal_failure(message, "fal_auth")
                return ProviderResult(
                    provider=self.name,
                    success=False,
                    error=user_msg,
                    metadata={"error_code": "fal_auth"},
                )
            return ProviderResult(
                provider=self.name,
                success=False,
                error=message,
            )
        except Exception as exc:
            message, status_code = _exception_details(exc)
            if is_fal_credit_failure(message, status_code):
                print(f"Fal API Error: {message}", flush=True)
                user_msg = classify_and_record_fal_failure(message, "fal_credit")
                logger.error("Fal API Error: %s", message)
                return ProviderResult(
                    provider=self.name,
                    success=False,
                    error=user_msg,
                    metadata={"error_code": "fal_credit"},
                )
            if is_fal_auth_failure(message, status_code):
                user_msg = classify_and_record_fal_failure(message, "fal_auth")
                logger.error("Fal auth error job=%s", job.job_id)
                return ProviderResult(
                    provider=self.name,
                    success=False,
                    error=user_msg,
                    metadata={"error_code": "fal_auth"},
                )
            classify_and_record_fal_failure(message or str(exc))
            print(f"Fal API Error: {message or exc}", flush=True)
            logger.exception("Fal generation failed job=%s", job.job_id)
            return ProviderResult(
                provider=self.name,
                success=False,
                error=f"Fal.ai generation failed: {exc}",
            )


def _build_fal_request(job: GenerationJobInput) -> tuple[str, dict[str, Any]]:
    prompt = _build_video_prompt(job)
    duration = _duration_for_fal(job.duration_seconds)
    image_path = job.driving_image_path
    wants_i2v = job.mode == "image" or image_path is not None

    arguments: dict[str, Any] = {
        "prompt": prompt,
        "duration": duration,
        "resolution": settings.fal_resolution,
        "enable_safety_checker": True,
    }

    if job.selected_endpoint:
        endpoint = job.selected_endpoint
    elif job.visual_style == "real":
        endpoint = settings.fal_model_real_face
        if image_path is None:
            raise ValueError(
                "Real face mode requires faceReference image uploaded to the server."
            )
    elif wants_i2v and image_path is not None:
        endpoint = settings.fal_model_i2v
    else:
        endpoint = settings.fal_model_t2v
        image_path = None

    if image_path is not None:
        if not image_path.exists():
            raise ValueError(f"Uploaded image not found: {image_path}")
        arguments["image_url"] = _resolve_image_url_for_fal(
            image_path,
            job.driving_image_public_url,
        )

    return endpoint, arguments


def _build_video_prompt(job: GenerationJobInput) -> str:
    parts: list[str] = []

    if job.main_prompt:
        parts.append(job.main_prompt)
    if job.lyrics:
        parts.append(f"Lyrics theme: {job.lyrics[:800]}")
    if job.music_style:
        parts.append(f"Music style: {job.music_style}")
    if job.direction_prompt:
        parts.append(job.direction_prompt)

    parts.append(f"Cinematic {job.category} video, {job.visual_style} style, high fidelity.")

    if job.visual_style == "real" and job.preserve_genuine_face:
        parts.append(
            "Maintain exact facial identity from reference image. "
            "No face morphing, no replacement. Natural skin texture, photorealistic."
        )
        if job.identity_strength:
            parts.append(f"Identity strength: {job.identity_strength:.2f}")

    if job.visual_style == "cartoon":
        parts.append("Vibrant animated cartoon, child-safe, consistent characters.")

    if job.visual_style == "avatar":
        parts.append("Professional presenter, studio lighting, stable identity.")

    return " ".join(parts).strip()[:2000]


def _duration_for_fal(duration_seconds: int) -> int:
    """Fal Wan 2.7 expects duration as int 2–15, not a string."""
    return max(_MIN_DURATION, min(_MAX_DURATION, int(duration_seconds)))


def _is_public_http_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    host = (parsed.hostname or "").lower()
    return host not in ("localhost", "127.0.0.1", "0.0.0.0")


def _cache_key_for_image(image_path: Path) -> str:
    stat = image_path.stat()
    raw = f"{image_path.resolve()}:{stat.st_size}:{int(stat.st_mtime)}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _read_upload_cache() -> dict[str, str]:
    if not _UPLOAD_CACHE_PATH.is_file():
        return {}
    try:
        return json.loads(_UPLOAD_CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_upload_cache(cache: dict[str, str]) -> None:
    _UPLOAD_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _UPLOAD_CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _resolve_image_url_for_fal(image_path: Path, public_url: str | None) -> str:
    if public_url and _is_public_http_url(public_url):
        logger.info("Using backend public image URL (no Fal upload charge): %s", public_url)
        return public_url

    cache_key = _cache_key_for_image(image_path)
    cached = _read_upload_cache().get(cache_key)
    if cached:
        logger.info("Reusing cached Fal image URL for %s", image_path.name)
        return cached

    uploaded_url = _upload_image_sync(image_path)
    cache = _read_upload_cache()
    cache[cache_key] = uploaded_url
    _write_upload_cache(cache)
    return uploaded_url


def _upload_image_sync(image_path: Path) -> str:
    assert_fal_live_allowed("fal-upload")
    try:
        uploaded = fal_client.upload_file(str(image_path))
    except Exception as exc:
        message, status_code = _exception_details(exc)
        if is_fal_credit_failure(message, status_code):
            raise ValueError(FAL_CREDIT_USER_MESSAGE) from exc
        if is_fal_auth_failure(message, status_code):
            raise ValueError(FAL_AUTH_USER_MESSAGE) from exc
        raise ValueError(f"Fal image upload failed: {message}") from exc
    if isinstance(uploaded, str):
        return uploaded
    url = getattr(uploaded, "url", None)
    if url:
        return str(url)
    if isinstance(uploaded, dict) and uploaded.get("url"):
        return str(uploaded["url"])
    raise ValueError(f"Fal upload returned unexpected shape: {uploaded!r}")


def _run_fal_subscribe_sync(endpoint: str, arguments: dict[str, Any]) -> Any:
    safe_args = _sanitize_fal_arguments(arguments)
    return fal_client.subscribe(
        endpoint,
        arguments=safe_args,
        with_logs=True,
    )


def _extract_video_url(result: Any) -> str | None:
    if result is None:
        return None

    if isinstance(result, dict):
        video = result.get("video")
        if isinstance(video, dict):
            url = video.get("url")
            if isinstance(url, str) and url.startswith("http"):
                return url
        url = result.get("url") or result.get("video_url")
        if isinstance(url, str) and url.startswith("http"):
            return url

    video_attr = getattr(result, "video", None)
    if video_attr is not None:
        url_attr = getattr(video_attr, "url", None)
        if isinstance(url_attr, str) and url_attr.startswith("http"):
            return url_attr

    return None

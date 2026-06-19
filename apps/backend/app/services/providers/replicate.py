"""
Replicate cloud GPU — Wan 2.1 I2V / T2V with async prediction polling.

Models (override via .env):
  - wavespeedai/wan-2.1-i2v-480p  (image → video)
  - wavespeedai/wan-2.1-t2v-480p  (text → video)
"""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, TYPE_CHECKING

import replicate
from replicate.exceptions import ReplicateError

from app.core.config import reload_settings, settings
from app.core.errors import (
    REPLICATE_AUTH_USER_MESSAGE,
    REPLICATE_CREDIT_USER_MESSAGE,
    is_replicate_auth_failure,
    is_replicate_credit_failure,
)
from app.services.providers.base import BaseAIProvider, ProviderResult

if TYPE_CHECKING:
    from app.services.ai_service import GenerationJobInput

logger = logging.getLogger(__name__)

# Wan 2.1 typical frame budget (~16 fps)
_FRAMES_PER_SECOND = 16
_MIN_FRAMES = 49
_MAX_FRAMES = 81


class ReplicateProvider(BaseAIProvider):
    name = "replicate"

    def is_configured(self) -> bool:
        return settings.replicate_configured

    def _client(self) -> replicate.Client:
        fresh = reload_settings()
        return replicate.Client(api_token=fresh.replicate_api_token)

    async def generate(self, job: GenerationJobInput) -> ProviderResult:
        if not self.is_configured():
            return ProviderResult(
                provider=self.name,
                success=False,
                error="REPLICATE_API_TOKEN not configured",
            )

        try:
            model_slug, model_input, image_path = _build_model_input(job)
            logger.info(
                "Replicate create job=%s model=%s routed_model=%s cost=$%.3f/s image=%s",
                job.job_id,
                model_slug,
                job.selected_model_id or "legacy",
                job.selected_cost_per_second or 0.0,
                bool(image_path),
            )

            prediction, output_url = await asyncio.to_thread(
                _run_prediction_sync,
                self._client(),
                model_slug,
                model_input,
                image_path,
            )

            return ProviderResult(
                provider=self.name,
                success=True,
                remote_url=output_url,
                external_job_id=prediction.id,
                metadata={
                    "model": model_slug,
                    "prediction_id": prediction.id,
                    "prediction_status": prediction.status,
                    "output_url": output_url,
                },
            )
        except ReplicateError as exc:
            status_code = getattr(exc, "status", None) or getattr(exc, "status_code", None)
            if is_replicate_auth_failure(str(exc), status_code):
                logger.error("Replicate auth error job=%s", job.job_id)
                return ProviderResult(
                    provider=self.name,
                    success=False,
                    error=REPLICATE_AUTH_USER_MESSAGE,
                    metadata={"error_code": "replicate_auth"},
                )
            if is_replicate_credit_failure(str(exc), status_code):
                logger.error("Replicate credit error job=%s", job.job_id)
                return ProviderResult(
                    provider=self.name,
                    success=False,
                    error=REPLICATE_CREDIT_USER_MESSAGE,
                    metadata={"error_code": "replicate_credit"},
                )
            logger.exception("Replicate API error job=%s", job.job_id)
            return ProviderResult(
                provider=self.name,
                success=False,
                error=f"Replicate API error: {exc}",
            )
        except TimeoutError as exc:
            return ProviderResult(
                provider=self.name,
                success=False,
                error=str(exc),
            )
        except Exception as exc:
            logger.exception("Replicate generation failed job=%s", job.job_id)
            return ProviderResult(
                provider=self.name,
                success=False,
                error=f"Replicate generation failed: {exc}",
            )


def _build_model_input(
    job: GenerationJobInput,
) -> tuple[str, dict[str, Any], Path | None]:
    """
    Map RTAS studio payload → Replicate model arguments.
    Returns (model_slug, input_dict, optional_image_path_for_file_upload).
    """
    prompt = _build_video_prompt(job)
    num_frames = _frames_for_duration(job.duration_seconds)

    image_path = job.driving_image_path
    wants_i2v = job.mode == "image" or image_path is not None

    if job.selected_endpoint:
        model_slug = job.selected_endpoint
    elif job.visual_style == "real":
        model_slug = settings.replicate_model_real_face
        if image_path is None:
            raise ValueError(
                "Real face mode requires faceReference image uploaded to the server. "
                f"Expected path under data/uploads/{job.job_id}/"
            )
    elif wants_i2v and image_path is not None:
        model_slug = settings.replicate_model_i2v
    else:
        model_slug = settings.replicate_model_t2v
        image_path = None

    model_input: dict[str, Any] = {
        "prompt": prompt,
        "num_frames": num_frames,
        "sample_guide_scale": 4,
        "sample_shift": 2,
    }

    return model_slug, model_input, image_path


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


def _frames_for_duration(duration_seconds: int) -> int:
    target = max(_MIN_FRAMES, min(_MAX_FRAMES, int(duration_seconds * _FRAMES_PER_SECOND)))
    return target


def _run_prediction_sync(
    client: replicate.Client,
    model: str,
    model_input: dict[str, Any],
    image_path: Path | None,
) -> tuple[Any, str]:
    """Blocking: create prediction, poll, return (prediction, mp4_url)."""
    if image_path and image_path.exists():
        with open(image_path, "rb") as image_file:
            payload = {**model_input, "image": image_file}
            prediction = client.predictions.create(model=model, input=payload)
    else:
        prediction = client.predictions.create(model=model, input=model_input)

    prediction = _poll_prediction(client, prediction.id)
    output_url = _extract_output_url(prediction.output)

    if not output_url:
        raise ValueError(f"Replicate returned no video URL. output={prediction.output!r}")

    return prediction, output_url


def _poll_prediction(client: replicate.Client, prediction_id: str) -> Any:
    deadline = time.monotonic() + settings.replicate_poll_timeout_sec
    prediction = client.predictions.get(prediction_id)

    while prediction.status in ("starting", "processing"):
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"Replicate prediction timed out after {settings.replicate_poll_timeout_sec}s"
            )
        time.sleep(settings.replicate_poll_interval_sec)
        prediction = client.predictions.get(prediction_id)

    if prediction.status == "failed":
        raise RuntimeError(prediction.error or "Replicate prediction failed")

    if prediction.status == "canceled":
        raise RuntimeError("Replicate prediction was canceled")

    return prediction


def _extract_output_url(output: Any) -> str | None:
    """Normalize Replicate output shapes to a single MP4/ media URL."""
    if output is None:
        return None

    if isinstance(output, str):
        return output if output.startswith("http") else None

    if isinstance(output, (list, tuple)):
        for item in output:
            url = _extract_output_url(item)
            if url:
                return url
        return None

    url_attr = getattr(output, "url", None)
    if callable(url_attr):
        try:
            return str(url_attr())
        except Exception:
            pass
    if isinstance(url_attr, str):
        return url_attr

    return str(output) if str(output).startswith("http") else None

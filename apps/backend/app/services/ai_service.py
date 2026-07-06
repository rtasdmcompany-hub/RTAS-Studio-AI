"""
RTAS Studio AI — core generation orchestration.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from app.core.config import reload_settings, settings
from app.core.errors import (
    FAL_AUTH_USER_MESSAGE,
    FAL_CREDIT_USER_MESSAGE,
    REPLICATE_AUTH_USER_MESSAGE,
    REPLICATE_CREDIT_USER_MESSAGE,
    is_fal_auth_failure,
    is_fal_credit_failure,
    is_replicate_auth_failure,
    is_replicate_credit_failure,
)
from app.schemas.generation import GenerateRequest, ProcessingStep, build_prompt_preview
from app.services.audio_probe import probe_audio_duration_seconds
from app.services.pipeline_simulation import (
    PREVIEW_PLACEHOLDER_VIDEO,
    build_processing_steps,
    resolve_output_flags,
    select_provider as select_ui_provider,
)
from app.services.providers.comfyui import ComfyUIProvider
from app.services.providers.diffusers_local import DiffusersInstantIDProvider
from app.services.providers.fal import FalProvider
from app.services.providers.replicate import ReplicateProvider
from app.services.content_moderation import (
    ContentPolicyViolation,
    assert_generate_request_allowed,
    assert_output_prompt_allowed,
)
from app.services.model_routing import (
    ModelRoutingError,
    apply_model_selection,
    select_optimal_model,
    weighted_credits_for_duration,
)
from app.services.storage import (
    ensure_dirs,
    job_output_path,
    publish_from_url,
    publish_local_mp4,
    resolve_upload_path,
)

logger = logging.getLogger(__name__)

ProviderName = Literal["simulation", "fal", "replicate", "comfyui", "diffusers"]


class LiveGenerationError(Exception):
    """Raised when live cloud generation fails (no simulation fallback)."""

    def __init__(
        self,
        message: str,
        provider_metadata: dict | None = None,
        error_code: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.provider_metadata = provider_metadata
        self.error_code = error_code


@dataclass
class IngestedAsset:
    field_id: str
    file_name: str
    mime_type: str
    size_bytes: int
    local_path: Path | None = None
    public_url: str | None = None

    @property
    def exists(self) -> bool:
        return self.local_path is not None and self.local_path.exists()


@dataclass
class GenerationJobInput:
    job_id: str
    mode: str
    category: str
    visual_style: str
    duration_seconds: int
    preview_only: bool
    use_free_trial: bool
    lyrics: str | None = None
    music_style: str | None = None
    main_prompt: str | None = None
    direction_prompt: str | None = None
    fields: dict[str, str] = field(default_factory=dict)
    assets: list[IngestedAsset] = field(default_factory=list)
    audio_source: IngestedAsset | None = None
    reference_image: IngestedAsset | None = None
    face_reference: IngestedAsset | None = None
    source_image: IngestedAsset | None = None
    identity_enabled: bool = False
    identity_provider: str = "instant-id"
    identity_strength: float = 0.85
    ip_adapter_enabled: bool = True
    instant_id_enabled: bool = True
    preserve_genuine_face: bool = True
    compiled_prompt: str = ""
    output_path: Path | None = None
    selected_model_id: str | None = None
    selected_model_name: str | None = None
    selected_endpoint: str | None = None
    selected_cost_per_second: float | None = None
    selection_reason: str | None = None
    credit_weight: float = 1.0
    status_callback_url: str | None = None
    pipeline_job_id: str | None = None
    pipeline_progress: object | None = field(default=None, repr=False)

    @property
    def face_reference_path(self) -> Path | None:
        if self.face_reference and self.face_reference.exists:
            return self.face_reference.local_path
        return None

    @property
    def driving_image_asset(self) -> IngestedAsset | None:
        for asset in (self.source_image, self.reference_image, self.face_reference):
            if asset and asset.exists:
                return asset
        return None

    @property
    def driving_image_path(self) -> Path | None:
        asset = self.driving_image_asset
        return asset.local_path if asset else None

    @property
    def driving_image_public_url(self) -> str | None:
        asset = self.driving_image_asset
        return asset.public_url if asset else None


@dataclass
class GenerationJobResult:
    job_id: str
    steps: list[ProcessingStep]
    provider: str
    prompt_preview: str
    preview_only: bool
    can_download: bool
    credits_used: int
    duration_seconds: int
    delivery_url: str
    local_mp4_path: Path | None = None
    simulation_mode: bool = False
    message: str = ""
    provider_metadata: dict | None = None


def _new_job_id() -> str:
    return f"job_{int(datetime.now(timezone.utc).timestamp() * 1000)}"


def ingest_payload(body: GenerateRequest, job_id: str | None = None) -> GenerationJobInput:
    ensure_dirs()
    jid = body.job_id or job_id or _new_job_id()
    assets: list[IngestedAsset] = []

    for field_id, meta in body.files.items():
        if meta.local_path:
            local = Path(meta.local_path)
            if not local.is_absolute():
                local = Path(meta.local_path).resolve()
        else:
            local = resolve_upload_path(jid, field_id, meta.name)
        assets.append(
            IngestedAsset(
                field_id=field_id,
                file_name=meta.name,
                mime_type=meta.mime_type,
                size_bytes=meta.size,
                local_path=local,
                public_url=meta.url,
            )
        )

    def pick(*ids: str) -> IngestedAsset | None:
        for fid in ids:
            for a in assets:
                if a.field_id == fid:
                    return a
        return None

    pipeline = body.identity_pipeline
    audio_source = pick("audioSource", "audio")

    resolved_duration = int(body.duration_seconds)
    if audio_source and audio_source.exists and audio_source.local_path:
        audio_len = probe_audio_duration_seconds(audio_source.local_path)
        if audio_len and audio_len > 0:
            resolved_duration = max(resolved_duration, int(round(audio_len)))
            # Business cap: full music videos up to 7 minutes
            resolved_duration = min(resolved_duration, 420)

    job = GenerationJobInput(
        job_id=jid,
        mode=body.mode,
        category=body.category,
        visual_style=body.visual_style,
        duration_seconds=resolved_duration,
        preview_only=body.preview_only,
        use_free_trial=body.use_free_trial,
        lyrics=body.fields.get("lyrics"),
        music_style=body.fields.get("musicStyle"),
        main_prompt=body.fields.get("mainPrompt"),
        direction_prompt=body.fields.get("directionPrompt") or body.fields.get("direction"),
        fields=dict(body.fields),
        assets=assets,
        audio_source=audio_source,
        reference_image=pick("referenceImage", "productImage", "coverImage"),
        face_reference=pick("faceReference"),
        source_image=pick("sourceImage"),
        identity_enabled=pipeline.enabled,
        identity_provider=pipeline.provider,
        identity_strength=pipeline.identity_strength,
        ip_adapter_enabled=pipeline.ip_adapter_enabled,
        instant_id_enabled=pipeline.instant_id_enabled,
        preserve_genuine_face=pipeline.preserve_genuine_face,
        output_path=job_output_path(jid),
    )
    job.compiled_prompt = _compile_prompt(job, body)
    job.status_callback_url = body.status_callback_url
    job.pipeline_job_id = body.pipeline_job_id
    return job


def _compile_prompt(job: GenerationJobInput, body: GenerateRequest) -> str:
    parts = [
        f"[{job.category}] mode={job.mode} style={job.visual_style}",
        f"duration={job.duration_seconds}s",
    ]
    if job.main_prompt:
        parts.append(job.main_prompt)
    if job.lyrics:
        parts.append(f"Lyrics:\n{job.lyrics}")
    if job.music_style:
        parts.append(f"Music style: {job.music_style}")
    if job.direction_prompt:
        parts.append(f"Direction: {job.direction_prompt}")
    if job.identity_enabled and job.preserve_genuine_face:
        parts.append(
            "Preserve exact facial identity; no morphing; photorealistic genuine likeness."
        )
    return "\n".join(parts)


def _pick_provider(job: GenerationJobInput) -> ProviderName:
    if job.preview_only:
        logger.info("Preview-only job=%s — simulation pipeline (no cloud spend)", job.job_id)
        return "simulation"

    mode = settings.ai_provider_mode

    if mode in ("comfyui", "diffusers", "fal", "replicate") and mode != "auto":
        if mode == "fal" and FalProvider().is_configured():
            return "fal"
        if mode == "replicate" and ReplicateProvider().is_configured():
            return "replicate"
        if mode == "comfyui" and ComfyUIProvider().is_configured():
            return "comfyui"
        if mode == "diffusers" and DiffusersInstantIDProvider().is_configured():
            return "diffusers"

    if settings.fal_configured:
        logger.info("FAL_KEY detected — live Fal.ai pipeline (simulation bypassed)")
        return "fal"

    if settings.replicate_configured:
        logger.info("REPLICATE_API_TOKEN detected — live Replicate pipeline (simulation bypassed)")
        return "replicate"

    if mode == "fal" and not FalProvider().is_configured():
        logger.info("FAL_KEY unset — falling back to simulation")
        return "simulation"
    if mode == "replicate" and not ReplicateProvider().is_configured():
        logger.info("REPLICATE_API_TOKEN unset — falling back to simulation")
        return "simulation"
    if mode not in ("auto", "fal", "replicate"):
        return mode  # type: ignore[return-value]

    if FalProvider().is_configured():
        return "fal"
    if ReplicateProvider().is_configured():
        return "replicate"
    if job.visual_style == "real" and DiffusersInstantIDProvider().is_configured():
        return "diffusers"
    if ComfyUIProvider().is_configured():
        return "comfyui"
    return "simulation"


async def _run_provider(job: GenerationJobInput, provider_name: ProviderName):
    if provider_name == "fal":
        return await FalProvider().generate(job)
    if provider_name == "replicate":
        return await ReplicateProvider().generate(job)
    if provider_name == "comfyui":
        return await ComfyUIProvider().generate(job)
    if provider_name == "diffusers":
        return await DiffusersInstantIDProvider().generate(job)
    return None


async def _simulation_delivery(job: GenerationJobInput) -> tuple[str, Path | None]:
    """Return frontend public sample path; browser loads it same-origin via Next.js."""
    return PREVIEW_PLACEHOLDER_VIDEO, None


async def run_generation(body: GenerateRequest) -> GenerationJobResult:
    reload_settings()
    assert_generate_request_allowed(body)
    job = ingest_payload(body, job_id=body.job_id)
    if body.status_callback_url and body.pipeline_job_id:
        from app.services.job_progress import PipelineProgressReporter

        job.pipeline_progress = PipelineProgressReporter(
            body.status_callback_url,
            body.pipeline_job_id,
        )
    assert_output_prompt_allowed(job.compiled_prompt)
    steps = build_processing_steps(body)
    preview_only, can_download, credits_used, _ = resolve_output_flags(body)
    duration = job.duration_seconds
    provider_name = _pick_provider(job)

    if (
        not preview_only
        and not body.use_free_trial
        and provider_name in ("fal", "replicate")
    ):
        try:
            selection = select_optimal_model(job, provider_name)
            apply_model_selection(job, selection)
            credits_used = weighted_credits_for_duration(
                duration, selection.cost_per_second
            )
            profile = body.profile
            if profile and profile.subscription_active and profile.credits < credits_used:
                needed = credits_used
                preview_only = True
                can_download = False
                credits_used = 0
                logger.info(
                    "Insufficient credits for weighted deduction job=%s need=%s have=%s",
                    job.job_id,
                    needed,
                    profile.credits,
                )
        except ModelRoutingError as exc:
            raise LiveGenerationError(str(exc), error_code="model_routing") from exc
    elif (
        not preview_only
        and not body.use_free_trial
        and duration > body.duration_seconds
    ):
        from app.services.pipeline_simulation import credits_for_duration

        credits_used = credits_for_duration(duration)

    ui_provider = job.selected_model_id or select_ui_provider(body)

    logger.info(
        "Generation start job=%s provider=%s ui_provider=%s model=%s weight=%.2fx",
        job.job_id,
        provider_name,
        ui_provider,
        job.selected_model_id or "auto",
        job.credit_weight,
    )

    delivery_url = PREVIEW_PLACEHOLDER_VIDEO
    local_path: Path | None = None
    simulation_mode = provider_name == "simulation"
    provider_meta: dict | None = None
    message = ""
    used_provider = ui_provider

    provider_result = await _run_provider(job, provider_name)

    if provider_result and provider_result.success:
        used_provider = job.selected_model_id or provider_result.provider
        simulation_mode = False
        if provider_result.local_mp4_path and provider_result.local_mp4_path.exists():
            local_path, delivery_url = publish_local_mp4(
                provider_result.local_mp4_path, job.job_id
            )
        elif provider_result.remote_url:
            local_path, delivery_url = await publish_from_url(
                provider_result.remote_url, job.job_id
            )
        message = f"Generated via {provider_result.provider} — cloud render complete"
        if job.selection_reason:
            message = f"{message} {job.selection_reason}"
        provider_meta = provider_result.metadata or {}
        if job.selected_model_id:
            provider_meta = {
                **provider_meta,
                "model_id": job.selected_model_id,
                "model_name": job.selected_model_name,
                "cost_per_second_usd": job.selected_cost_per_second,
                "credit_weight": job.credit_weight,
                "selection_reason": job.selection_reason,
            }
    else:
        if provider_result and provider_result.error:
            logger.warning("Provider %s: %s", provider_name, provider_result.error)
            provider_meta = {
                "provider_error": provider_result.error,
                **(provider_result.metadata or {}),
            }

        live_provider = provider_name in ("fal", "replicate")
        live_configured = (
            (provider_name == "fal" and settings.fal_configured)
            or (provider_name == "replicate" and settings.replicate_configured)
        )
        if live_provider and live_configured:
            error_msg = (
                provider_result.error
                if provider_result and provider_result.error
                else f"{provider_name} generation failed"
            )
            error_code = (
                provider_meta.get("error_code")
                if provider_meta and isinstance(provider_meta.get("error_code"), str)
                else None
            )
            if error_code == "fal_credit" or is_fal_credit_failure(error_msg):
                error_code = "fal_credit"
                error_msg = FAL_CREDIT_USER_MESSAGE
            elif error_code == "fal_auth" or is_fal_auth_failure(error_msg):
                error_code = "fal_auth"
                error_msg = FAL_AUTH_USER_MESSAGE
            elif error_code == "replicate_auth" or is_replicate_auth_failure(error_msg):
                error_code = "replicate_auth"
                error_msg = REPLICATE_AUTH_USER_MESSAGE
            elif error_code == "replicate_credit" or is_replicate_credit_failure(error_msg):
                error_code = "replicate_credit"
                error_msg = REPLICATE_CREDIT_USER_MESSAGE
            raise LiveGenerationError(error_msg, provider_meta, error_code=error_code)

        sim_url, _ = await _simulation_delivery(job)
        delivery_url = sim_url
        simulation_mode = True
        message = (
            "Preview ready — watch your draft while the full render queue opens."
            if job.preview_only
            else (
                f"RTAS AI pipeline complete ({provider_name} → simulation). "
                f"Set FAL_KEY for cloud renders."
            )
        )

    if local_path is None and not simulation_mode:
        simulation_mode = delivery_url == PREVIEW_PLACEHOLDER_VIDEO

    # Bill RTAS credits only after a successful live (non-simulation) render.
    billable_success = (
        provider_result is not None
        and provider_result.success
        and not simulation_mode
        and not preview_only
    )
    final_credits_used = credits_used if billable_success else 0

    return GenerationJobResult(
        job_id=job.job_id,
        steps=steps,
        provider=used_provider,
        prompt_preview=build_prompt_preview(body),
        preview_only=preview_only,
        can_download=can_download and billable_success,
        credits_used=final_credits_used,
        duration_seconds=duration,
        delivery_url=delivery_url,
        local_mp4_path=local_path,
        simulation_mode=simulation_mode,
        message=message,
        provider_metadata=provider_meta,
    )

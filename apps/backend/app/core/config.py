from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BackendRoot = Path(__file__).resolve().parents[2]


def _env_file_paths() -> tuple[Path, ...]:
    """Backend .env first; outer monorepo apps/api/.env as fallback for shared keys."""
    paths: list[Path] = [BackendRoot / ".env"]
    outer_api_env = BackendRoot.parent.parent.parent / "apps" / "api" / ".env"
    if outer_api_env.is_file():
        paths.append(outer_api_env)
    return tuple(paths)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_file_paths(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001"

    # AI provider credentials (empty string → unset → simulation fallback)
    replicate_api_token: str | None = None
    ai_backend_secret: str | None = None
    generation_webhook_secret: str | None = Field(
        default=None, validation_alias="RTAS_GENERATION_WEBHOOK_SECRET"
    )
    comfyui_api_url: str | None = None
    comfyui_api_key: str | None = None
    fal_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("FAL_KEY", "FAL_API_KEY"),
    )
    runway_api_key: str | None = None
    kling_api_key: str | None = None

    # Fal.ai model endpoints (Wan 2.7 — override per deploy)
    fal_model_i2v: str = "fal-ai/wan/v2.7/image-to-video"
    fal_model_t2v: str = "fal-ai/wan/v2.7/text-to-video"
    fal_model_real_face: str = "fal-ai/wan/v2.7/image-to-video"
    fal_model_flashhead: str = "fal-ai/flash-head"
    fal_model_cinematic: str = "fal-ai/wan/v2.7/image-to-video"
    fal_resolution: str = "720p"

    # Tier-routed Fal endpoints (billing separation — override per deploy)
    fal_tier_economy_t2v: str = "fal-ai/mochi-video"
    fal_tier_economy_i2v: str = "fal-ai/mochi-video"
    fal_tier_economy_real_face: str = "fal-ai/mochi-video"
    fal_tier_economy_resolution: str = "720p"
    fal_tier_enterprise_t2v: str = "fal-ai/kling-video"
    fal_tier_enterprise_i2v: str = "fal-ai/kling-video"
    fal_tier_enterprise_real_face: str = "fal-ai/kling-video"
    fal_tier_enterprise_cinematic: str = "fal-ai/luma-dream-machine"
    fal_tier_enterprise_resolution: str = "1080p"
    fal_strict_tier_routing: bool = Field(
        default=True, validation_alias="FAL_STRICT_TIER_ROUTING"
    )
    # Owner wallet protection — no live Fal calls when false (zero Fal spend)
    fal_live_enabled: bool = Field(default=True, validation_alias="FAL_LIVE_ENABLED")
    fal_retry_cooldown_sec: int = Field(
        default=300, validation_alias="FAL_RETRY_COOLDOWN_SEC"
    )
    fal_strict_billing_guard: bool = Field(
        default=True, validation_alias="FAL_STRICT_BILLING_GUARD"
    )
    fal_max_failures_before_block: int = Field(
        default=1, validation_alias="FAL_MAX_FAILURES_BEFORE_BLOCK"
    )

    # Replicate model slugs (legacy fallback)
    replicate_model_i2v: str = "wavespeedai/wan-2.1-i2v-480p"
    replicate_model_t2v: str = "wavespeedai/wan-2.1-t2v-480p"
    replicate_model_real_face: str = "wavespeedai/wan-2.1-i2v-480p"
    replicate_poll_interval_sec: float = 2.0
    replicate_poll_timeout_sec: int = 600
    replicate_cache_outputs_locally: bool = True

    # Local Diffusers / InstantID (future worker)
    diffusers_enabled: bool = False
    diffusers_device: str = "cuda"
    instantid_model_path: str | None = None

    # Routing: simulation | fal | replicate | comfyui | diffusers | auto
    ai_provider_mode: Literal[
        "simulation", "fal", "replicate", "comfyui", "diffusers", "auto"
    ] = "auto"

    # Storage
    storage_mode: Literal["local", "s3", "r2"] = "local"
    local_upload_dir: Path = Field(default=BackendRoot / "data" / "uploads")
    local_output_dir: Path = Field(default=BackendRoot / "data" / "outputs")
    public_base_url: str = "http://localhost:8000"

    # Upload limits
    max_upload_bytes: int = 52_428_800  # 50 MB
    allowed_image_mimes: str = "image/jpeg,image/png,image/webp,image/gif"
    allowed_audio_mimes: str = "audio/mpeg,audio/wav,audio/mp4,audio/x-m4a,audio/mpeg3"

    # S3 / R2 (future)
    s3_bucket: str | None = None
    s3_region: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_public_base_url: str | None = None

    @field_validator(
        "replicate_api_token",
        "comfyui_api_key",
        "fal_key",
        "runway_api_key",
        "kling_api_key",
        "ai_backend_secret",
        "generation_webhook_secret",
        mode="before",
    )
    @classmethod
    def empty_str_to_none(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def fal_configured(self) -> bool:
        return bool(self.fal_key and str(self.fal_key).strip())

    @property
    def replicate_configured(self) -> bool:
        return bool(self.replicate_api_token and str(self.replicate_api_token).strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    """Re-read .env files so token updates apply without a full server restart."""
    global settings
    get_settings.cache_clear()
    settings = get_settings()
    return settings


settings = get_settings()

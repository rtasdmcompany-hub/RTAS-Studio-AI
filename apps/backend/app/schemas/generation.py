from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


VisualStyle = Literal["real", "avatar", "cartoon"]
GenerationMode = Literal["prompt", "image"]
VideoCategory = Literal[
    "song", "religious", "business", "cartoon", "story", "podcast"
]
IdentityProvider = Literal["instant-id", "ip-adapter", "kling-character-id"]


class IdentityPipelineConfig(BaseModel):
    enabled: bool = False
    provider: IdentityProvider = "instant-id"
    identity_strength: float = Field(0.85, alias="identityStrength")
    ip_adapter_enabled: bool = Field(True, alias="ipAdapterEnabled")
    instant_id_enabled: bool = Field(True, alias="instantIdEnabled")
    face_reference_field_id: str = Field("faceReference", alias="faceReferenceFieldId")
    preserve_genuine_face: bool = Field(True, alias="preserveGenuineFace")

    model_config = {"populate_by_name": True}


class FileMeta(BaseModel):
    name: str
    mime_type: str = Field(alias="mimeType")
    size: int
    local_path: Optional[str] = Field(None, alias="localPath")
    url: Optional[str] = None

    model_config = {"populate_by_name": True}


class UserProfileSnapshot(BaseModel):
    subscription_active: bool = Field(False, alias="subscriptionActive")
    credits: int = 0
    free_trial_used: bool = Field(False, alias="freeTrialUsed")
    has_used_free_trial: bool = Field(False, alias="hasUsedFreeTrial")
    tier: Optional[str] = "free"

    model_config = {"populate_by_name": True}


class GenerateRequest(BaseModel):
    """Mirrors Next.js `buildGeneratePayload` + generation flags."""

    job_id: Optional[str] = Field(None, alias="jobId")
    mode: GenerationMode
    category: VideoCategory
    visual_style: VisualStyle = Field(alias="visualStyle")
    duration_seconds: int = Field(30, alias="durationSeconds")
    fields: dict[str, str] = Field(default_factory=dict)
    files: dict[str, FileMeta] = Field(default_factory=dict)
    identity_pipeline: IdentityPipelineConfig = Field(
        default_factory=IdentityPipelineConfig, alias="identityPipeline"
    )
    profile: Optional[UserProfileSnapshot] = None
    preview_only: bool = Field(False, alias="previewOnly")
    use_free_trial: bool = Field(False, alias="useFreeTrial")
    device_fingerprint: Optional[str] = Field(None, alias="deviceFingerprint")
    user_id: Optional[str] = Field(None, alias="userId")

    model_config = {"populate_by_name": True}

    @field_validator("duration_seconds", mode="before")
    @classmethod
    def coerce_duration_seconds(cls, value: Any) -> int:
        if value is None or value == "":
            return 15
        try:
            parsed = int(float(str(value).strip()))
        except (TypeError, ValueError):
            return 15
        return max(5, min(600, parsed))


class ProcessingStep(BaseModel):
    percent: int
    message: str
    stage_index: int = Field(alias="stageIndex")

    model_config = {"populate_by_name": True, "by_alias": True}


class GenerateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    ok: bool = True
    job_id: str = Field(alias="jobId")
    steps: list[ProcessingStep]
    provider: str
    prompt_preview: str = Field(alias="promptPreview")
    credits_used: int = Field(alias="creditsUsed")
    preview_only: bool = Field(alias="previewOnly")
    can_download: bool = Field(alias="canDownload")
    video_url: str = Field(alias="videoUrl")
    duration_seconds: int = Field(alias="durationSeconds")
    message: str
    simulation_mode: bool = Field(False, alias="simulationMode")
    asset_path: Optional[str] = Field(None, alias="assetPath")
    storage_key: Optional[str] = Field(None, alias="storageKey")


def build_prompt_preview(body: GenerateRequest) -> str:
    parts = [
        f"Category: {body.category}",
        f"Mode: {body.mode}",
        f"Style: {body.visual_style}",
        f"Duration: {body.duration_seconds}s",
    ]
    if body.fields.get("mainPrompt"):
        parts.append(body.fields["mainPrompt"])
    if body.fields.get("lyrics"):
        parts.append(f"Lyrics: {body.fields['lyrics'][:120]}…")
    if body.fields.get("musicStyle"):
        parts.append(f"Music style: {body.fields['musicStyle']}")
    if body.identity_pipeline.enabled:
        parts.append(
            f"Pipeline: {body.identity_pipeline.provider} "
            f"(strength={body.identity_pipeline.identity_strength})"
        )
    return "\n".join(parts)[:500]

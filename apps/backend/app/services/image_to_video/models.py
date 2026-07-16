"""Models for Image-to-Video Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ImageRole = Literal[
    "single",
    "multiple",
    "reference",
    "character",
    "product",
    "logo",
]
RequestState = Literal[
    "planned",
    "queued",
    "running",
    "completed",
    "failed",
    "retrying",
    "cancelled",
]
JobState = Literal["planned", "queued", "running", "completed", "failed", "partial"]


@dataclass
class ImageAsset:
    image_id: str
    role: ImageRole
    url: str | None = None
    local_path: str | None = None
    label: str = ""
    mime_type: str | None = None
    width: int | None = None
    height: int | None = None
    source_field: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def resolved_uri(self) -> str:
        return (self.url or self.local_path or "").strip()


@dataclass
class ImageValidationIssue:
    code: str
    severity: Literal["error", "warning", "info"]
    message: str
    image_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ImageValidationResult:
    passed: bool
    score: float
    issues: list[ImageValidationIssue] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score,
            "issues": [i.to_dict() for i in self.issues],
            "checks": self.checks,
        }


@dataclass
class ImageMetadataRecord:
    image_id: str
    role: ImageRole
    uri: str
    label: str
    aspect_hint: str
    preserve: dict[str, bool]
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SceneImageBinding:
    scene_number: int
    scene_id: str
    primary_image_id: str
    reference_image_ids: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class I2VProviderRequest:
    request_id: str
    job_id: str
    scene_number: int
    shot_number: int
    prompt: str
    duration_seconds: float
    primary_image_url: str
    reference_image_urls: list[str] = field(default_factory=list)
    provider_hint: str | None = None
    model_hint: str = "image-to-video"
    aspect: str = "landscape"
    resolution: str = "1080p"
    negative_prompt: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    state: RequestState = "planned"
    attempts: int = 0
    max_attempts: int = 3
    error: str | None = None
    result_url: str | None = None
    external_job_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_provider_payload(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "job_id": self.job_id,
            "mode": "image",
            "scene_number": self.scene_number,
            "shot_number": self.shot_number,
            "compiled_prompt": self.prompt,
            "main_prompt": self.prompt,
            "duration_seconds": max(2, int(round(self.duration_seconds))),
            "image_url": self.primary_image_url,
            "reference_image_urls": list(self.reference_image_urls),
            "provider_hint": self.provider_hint,
            "model_hint": self.model_hint,
            "negative_prompt": self.negative_prompt,
            "arguments": {
                "prompt": self.prompt,
                "image_url": self.primary_image_url,
                "duration": max(2, int(round(self.duration_seconds))),
                "aspect": self.aspect,
                "resolution": self.resolution,
                **self.arguments,
            },
            "metadata": dict(self.metadata),
        }


@dataclass
class ImageToVideoJob:
    job_id: str
    parent_generation_id: str | None
    prompt: str
    state: JobState
    images: list[ImageAsset]
    image_metadata: list[ImageMetadataRecord]
    validation: ImageValidationResult
    scene_bindings: list[SceneImageBinding]
    requests: list[I2VProviderRequest]
    preserve: dict[str, bool] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "parent_generation_id": self.parent_generation_id,
            "prompt": self.prompt,
            "state": self.state,
            "images": [i.to_dict() for i in self.images],
            "image_metadata": [m.to_dict() for m in self.image_metadata],
            "validation": self.validation.to_dict(),
            "scene_bindings": [b.to_dict() for b in self.scene_bindings],
            "requests": [r.to_dict() for r in self.requests],
            "preserve": self.preserve,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "state": self.state,
            "images": len(self.images),
            "scenes": len(self.scene_bindings),
            "requests": len(self.requests),
            "validation_passed": self.validation.passed,
            "queued": sum(1 for r in self.requests if r.state == "queued"),
            "completed": sum(1 for r in self.requests if r.state == "completed"),
            "failed": sum(1 for r in self.requests if r.state == "failed"),
            "roles": sorted({i.role for i in self.images}),
        }


@dataclass
class HistoryRecord:
    history_id: str
    job_id: str
    request_id: str | None
    event: str
    timestamp: str
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.5
    backoff_multiplier: float = 2.0
    retryable_error_substrings: tuple[str, ...] = (
        "timeout",
        "rate limit",
        "temporarily",
        "unavailable",
        "503",
        "429",
        "connection",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_attempts": self.max_attempts,
            "base_delay_seconds": self.base_delay_seconds,
            "backoff_multiplier": self.backoff_multiplier,
            "retryable_error_substrings": list(self.retryable_error_substrings),
        }

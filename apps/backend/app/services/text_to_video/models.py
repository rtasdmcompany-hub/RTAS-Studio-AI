"""Models for Real Text-to-Video Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

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
class ShotMetadata:
    shot_id: str
    scene_number: int
    shot_number: int
    shot_type: str
    duration_seconds: float
    camera_angle: str = ""
    lens: str = ""
    camera_movement: str = ""
    lighting: list[str] = field(default_factory=list)
    environment: str = ""
    weather: str = ""
    time: str = ""
    character_emotion: str = ""
    purpose: str = ""
    transition_type: str = "cut"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SceneMetadata:
    scene_id: str
    scene_number: int
    title: str
    purpose: str
    duration_seconds: float
    environment: str = ""
    weather: str = ""
    time: str = ""
    character_emotion: str = ""
    shot_ids: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderGenerationRequest:
    """One provider-ready generation request (typically one shot clip)."""

    request_id: str
    job_id: str
    scene_id: str
    shot_id: str
    scene_number: int
    shot_number: int
    prompt: str
    duration_seconds: float
    provider_hint: str | None = None
    aspect: str = "landscape"
    resolution: str = "1080p"
    hdr: bool = False
    negative_prompt: str = ""
    identity_lock: str = ""
    reference_image_urls: list[str] = field(default_factory=list)
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
        """Shape consumed by provider orchestrator / GenerationJobInput fields."""
        return {
            "request_id": self.request_id,
            "job_id": self.job_id,
            "scene_number": self.scene_number,
            "shot_number": self.shot_number,
            "compiled_prompt": self.prompt,
            "main_prompt": self.prompt,
            "duration_seconds": max(2, int(round(self.duration_seconds))),
            "provider_hint": self.provider_hint,
            "negative_prompt": self.negative_prompt,
            "identity_lock": self.identity_lock,
            "reference_image_urls": list(self.reference_image_urls),
            "arguments": {
                "prompt": self.prompt,
                "duration": max(2, int(round(self.duration_seconds))),
                "aspect": self.aspect,
                "resolution": self.resolution,
                "hdr": self.hdr,
                **self.arguments,
            },
            "metadata": {
                "scene_id": self.scene_id,
                "shot_id": self.shot_id,
                **self.metadata,
            },
        }


@dataclass
class TextToVideoJob:
    job_id: str
    parent_generation_id: str | None
    prompt: str
    state: JobState
    scenes: list[SceneMetadata]
    shots: list[ShotMetadata]
    requests: list[ProviderGenerationRequest]
    character_memory: list[dict[str, Any]] = field(default_factory=list)
    director_notes: list[str] = field(default_factory=list)
    production_package_snapshot: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "parent_generation_id": self.parent_generation_id,
            "prompt": self.prompt,
            "state": self.state,
            "scenes": [s.to_dict() for s in self.scenes],
            "shots": [s.to_dict() for s in self.shots],
            "requests": [r.to_dict() for r in self.requests],
            "character_memory": self.character_memory,
            "director_notes": self.director_notes,
            "production_package_snapshot": self.production_package_snapshot,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "state": self.state,
            "scenes": len(self.scenes),
            "shots": len(self.shots),
            "requests": len(self.requests),
            "queued": sum(1 for r in self.requests if r.state == "queued"),
            "completed": sum(1 for r in self.requests if r.state == "completed"),
            "failed": sum(1 for r in self.requests if r.state == "failed"),
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

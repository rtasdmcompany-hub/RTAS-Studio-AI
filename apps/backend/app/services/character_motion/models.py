"""Character motion domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

MotionJobState = Literal[
    "queued",
    "preparing",
    "motion_planning",
    "pose_generation",
    "animation",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]

EmotionTone = Literal[
    "happy",
    "sad",
    "angry",
    "romantic",
    "serious",
    "motivational",
    "fear",
    "suspense",
    "excited",
    "calm",
]

BODY_PRESERVED_TRAITS = (
    "face_identity",
    "body_shape",
    "height",
    "weight",
    "body_proportions",
    "walking_style",
    "running_style",
    "gesture_style",
    "eye_contact",
    "head_movement",
)


@dataclass
class CharacterMotionProfile:
    character_id: str
    face_identity_ref: str | None
    body_shape: str
    height: str
    weight: str
    body_proportions: str
    walking_style: str
    running_style: str
    gesture_style: str
    eye_contact: str
    head_movement: str
    dna_fingerprint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def fingerprint(self) -> str:
        import hashlib

        payload = "|".join(
            [
                self.character_id,
                self.face_identity_ref or "",
                self.body_shape,
                self.height,
                self.weight,
                self.body_proportions,
                self.walking_style,
                self.running_style,
                self.gesture_style,
                self.eye_contact,
                self.head_movement,
            ]
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:24]


@dataclass
class PoseKeyframe:
    pose_id: str
    name: str
    joints: dict[str, Any]
    timestamp_sec: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MotionClip:
    clip_id: str
    action: str
    emotion: EmotionTone
    duration_sec: float
    poses: list[PoseKeyframe] = field(default_factory=list)
    hand_gestures: list[dict[str, Any]] = field(default_factory=list)
    head_motion: dict[str, Any] = field(default_factory=dict)
    eye_motion: dict[str, Any] = field(default_factory=dict)
    facial_expression: dict[str, Any] = field(default_factory=dict)
    locomotion: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "clip_id": self.clip_id,
            "action": self.action,
            "emotion": self.emotion,
            "duration_sec": self.duration_sec,
            "poses": [p.to_dict() for p in self.poses],
            "hand_gestures": list(self.hand_gestures),
            "head_motion": dict(self.head_motion),
            "eye_motion": dict(self.eye_motion),
            "facial_expression": dict(self.facial_expression),
            "locomotion": dict(self.locomotion),
            "metadata": dict(self.metadata),
        }


@dataclass
class MotionTimelineEvent:
    event_id: str
    start_sec: float
    end_sec: float
    action: str
    clip_id: str
    layer: str = "body"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BodyConsistencyReport:
    character_id: str
    consistent: bool
    score: float
    preserved_traits: list[str] = field(default_factory=list)
    drift_flags: list[str] = field(default_factory=list)
    no_body_distortion: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MotionObservability:
    motion_job_id: str
    character_id: str | None = None
    animation_duration_sec: float = 0.0
    processing_time_ms: float = 0.0
    queue_time_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CharacterMotionJob:
    job_id: str
    state: MotionJobState
    character_id: str | None
    profile: CharacterMotionProfile | None
    actions: list[str]
    emotion: EmotionTone
    duration_sec: float
    clips: list[MotionClip] = field(default_factory=list)
    timeline: list[MotionTimelineEvent] = field(default_factory=list)
    consistency: BodyConsistencyReport | None = None
    integrations: dict[str, Any] = field(default_factory=dict)
    observability: MotionObservability | None = None
    queue_position: int | None = None
    retry_count: int = 0
    production_ready: bool = True
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "state": self.state,
            "character_id": self.character_id,
            "actions": list(self.actions),
            "emotion": self.emotion,
            "duration_sec": self.duration_sec,
            "clip_count": len(self.clips),
            "timeline_events": len(self.timeline),
            "queue_position": self.queue_position,
            "retry_count": self.retry_count,
            "production_ready": self.production_ready,
            "consistency_score": self.consistency.score if self.consistency else None,
            "consistent": self.consistency.consistent if self.consistency else None,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "profile": self.profile.to_dict() if self.profile else None,
            "clips": [c.to_dict() for c in self.clips],
            "timeline": [t.to_dict() for t in self.timeline],
            "consistency": self.consistency.to_dict() if self.consistency else None,
            "integrations": dict(self.integrations),
            "observability": self.observability.to_dict() if self.observability else None,
            "metadata": dict(self.metadata),
            "error": self.error,
            "version": self.version,
        }

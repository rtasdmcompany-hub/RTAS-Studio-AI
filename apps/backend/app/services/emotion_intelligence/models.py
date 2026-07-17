"""Emotion / expression / performance domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

EmotionJobState = Literal[
    "queued",
    "preparing",
    "emotion_analysis",
    "expression_generation",
    "performance_optimization",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]

IDENTITY_SAFE_TRAITS = (
    "face_structure",
    "eye_shape_base",
    "skin_tone",
    "character_id",
    "face_embedding_ref",
)


@dataclass
class FacialExpression:
    emotion: str
    eye_movement: dict[str, Any]
    eyebrow_movement: dict[str, Any]
    mouth_expression: dict[str, Any]
    smile_intensity: float
    lip_movement: dict[str, Any]
    cheek_movement: dict[str, Any]
    forehead_movement: dict[str, Any]
    head_tilt: dict[str, Any]
    eye_contact: dict[str, Any]
    blink_timing: dict[str, Any]
    expression_score: float = 100.0
    face_lock_respected: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BodyPerformance:
    emotion: str
    hand_gestures: list[dict[str, Any]]
    walking_style: str
    standing_pose: str
    sitting_pose: str
    head_movement: dict[str, Any]
    shoulder_movement: dict[str, Any]
    body_balance: dict[str, Any]
    natural_breathing: dict[str, Any]
    intensity: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EmotionProfile:
    character_id: str | None
    primary_emotion: str
    secondary_emotion: str | None
    intensity: float
    face_embedding_ref: str | None = None
    dna_fingerprint: str | None = None
    memory_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EmotionAnalysis:
    scene_emotion: str
    dialogue_emotion: str
    story_emotion: str
    character_emotion: str
    emotional_transition: str
    performance_intensity: float
    recommendations: list[str] = field(default_factory=list)
    confidence: float = 0.85

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EmotionTimelineEvent:
    event_id: str
    start_sec: float
    end_sec: float
    emotion: str
    intensity: float
    expression_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConsistencyReport:
    character_id: str | None
    consistent: bool
    expression_score: float
    identity_preserved: bool
    emotion_continuity: bool
    drift_flags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EmotionObservability:
    emotion_job_id: str
    character_id: str | None = None
    emotion_type: str | None = None
    expression_score: float = 0.0
    processing_time_ms: float = 0.0
    queue_time_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EmotionIntelligenceJob:
    job_id: str
    state: EmotionJobState
    prompt: str
    character_id: str | None
    analysis: EmotionAnalysis | None = None
    profile: EmotionProfile | None = None
    expression: FacialExpression | None = None
    performance: BodyPerformance | None = None
    timeline: list[EmotionTimelineEvent] = field(default_factory=list)
    consistency: ConsistencyReport | None = None
    integrations: dict[str, Any] = field(default_factory=dict)
    observability: EmotionObservability | None = None
    queue_position: int | None = None
    retry_count: int = 0
    production_ready: bool = True
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_sec: float = 4.0

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "state": self.state,
            "character_id": self.character_id,
            "primary_emotion": self.profile.primary_emotion if self.profile else None,
            "expression_score": (
                self.expression.expression_score if self.expression else None
            ),
            "duration_sec": self.duration_sec,
            "timeline_events": len(self.timeline),
            "queue_position": self.queue_position,
            "retry_count": self.retry_count,
            "production_ready": self.production_ready,
            "consistent": self.consistency.consistent if self.consistency else None,
            "identity_preserved": (
                self.consistency.identity_preserved if self.consistency else None
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "prompt": self.prompt,
            "analysis": self.analysis.to_dict() if self.analysis else None,
            "profile": self.profile.to_dict() if self.profile else None,
            "expression": self.expression.to_dict() if self.expression else None,
            "performance": self.performance.to_dict() if self.performance else None,
            "timeline": [t.to_dict() for t in self.timeline],
            "consistency": self.consistency.to_dict() if self.consistency else None,
            "integrations": dict(self.integrations),
            "observability": self.observability.to_dict() if self.observability else None,
            "metadata": dict(self.metadata),
            "error": self.error,
            "version": self.version,
        }

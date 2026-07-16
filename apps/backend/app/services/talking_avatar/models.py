"""Models for Talking Avatar Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

JobState = Literal["planned", "ready", "failed"]


@dataclass
class FaceLock:
    character_id: str
    reference_face_url: str | None
    face_locked: bool
    identity_strength: float
    locked_traits: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LipSyncFrame:
    start_sec: float
    end_sec: float
    viseme: str
    phoneme_hint: str
    mouth_openness: float
    jaw_drop: float
    dialogue_snippet: str = ""
    sync_confidence: float = 0.8

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HeadMotionCue:
    start_sec: float
    end_sec: float
    yaw: float  # -1..1
    pitch: float
    roll: float
    intensity: float
    kind: str  # nod, turn, idle, emphasis

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EyeContactCue:
    start_sec: float
    end_sec: float
    gaze_x: float  # -1..1
    gaze_y: float
    blink: bool
    eyelid_close: float  # 0 open .. 1 closed
    kind: str  # contact, glance, blink, lookaway

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExpressionCue:
    start_sec: float
    end_sec: float
    emotion: str
    smile: float  # 0..1
    brow_raise: float
    intensity: float
    kind: str  # speak, smile, idle, react

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IdleMotionCue:
    start_sec: float
    end_sec: float
    sway: float
    micro_nod: float
    breath: float
    kind: str = "idle"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AvatarTimeline:
    runtime_seconds: float
    lip_sync: list[LipSyncFrame]
    head_motion: list[HeadMotionCue]
    eye_contact: list[EyeContactCue]
    expressions: list[ExpressionCue]
    idle_motion: list[IdleMotionCue]
    blinks: list[EyeContactCue] = field(default_factory=list)
    smiles: list[ExpressionCue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime_seconds": self.runtime_seconds,
            "lip_sync": [c.to_dict() for c in self.lip_sync],
            "head_motion": [c.to_dict() for c in self.head_motion],
            "eye_contact": [c.to_dict() for c in self.eye_contact],
            "expressions": [c.to_dict() for c in self.expressions],
            "idle_motion": [c.to_dict() for c in self.idle_motion],
            "blinks": [c.to_dict() for c in self.blinks],
            "smiles": [c.to_dict() for c in self.smiles],
        }


@dataclass
class AvatarProviderRequest:
    request_id: str
    job_id: str
    prompt: str
    duration_seconds: float
    face_reference_url: str | None
    audio_hint: str | None = None
    emotion: str = "neutral"
    identity_strength: float = 0.9
    arguments: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_provider_payload(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "job_id": self.job_id,
            "mode": "avatar",
            "visual_style": "avatar",
            "compiled_prompt": self.prompt,
            "main_prompt": self.prompt,
            "duration_seconds": max(2, int(round(self.duration_seconds))),
            "face_reference_url": self.face_reference_url,
            "identity_strength": self.identity_strength,
            "emotion": self.emotion,
            "arguments": {
                "prompt": self.prompt,
                "image_url": self.face_reference_url,
                "duration": max(2, int(round(self.duration_seconds))),
                "talking_head": True,
                "lip_sync": True,
                **self.arguments,
            },
            "metadata": dict(self.metadata),
        }


@dataclass
class TalkingAvatarJob:
    job_id: str
    parent_generation_id: str | None
    prompt: str
    state: JobState
    face_lock: FaceLock
    timeline: AvatarTimeline
    emotion: str
    natural_motion: bool
    director_notes: list[str]
    character_memory: list[dict[str, Any]]
    provider_request: AvatarProviderRequest | None
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "parent_generation_id": self.parent_generation_id,
            "prompt": self.prompt,
            "state": self.state,
            "face_lock": self.face_lock.to_dict(),
            "timeline": self.timeline.to_dict(),
            "emotion": self.emotion,
            "natural_motion": self.natural_motion,
            "director_notes": self.director_notes,
            "character_memory": self.character_memory,
            "provider_request": (
                self.provider_request.to_dict() if self.provider_request else None
            ),
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    def summary(self) -> dict[str, Any]:
        tl = self.timeline
        return {
            "job_id": self.job_id,
            "state": self.state,
            "emotion": self.emotion,
            "face_locked": self.face_lock.face_locked,
            "runtime_seconds": tl.runtime_seconds,
            "lip_sync_cues": len(tl.lip_sync),
            "head_motion_cues": len(tl.head_motion),
            "eye_contact_cues": len(tl.eye_contact),
            "blinks": len(tl.blinks),
            "smiles": len(tl.smiles),
            "idle_cues": len(tl.idle_motion),
            "natural_motion": self.natural_motion,
        }

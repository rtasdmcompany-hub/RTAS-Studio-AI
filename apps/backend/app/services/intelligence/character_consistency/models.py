"""Models for Character Consistency Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

SubjectKind = Literal[
    "single_character",
    "two_characters",
    "family",
    "crowd",
    "animal",
    "vehicle",
]

DriftKind = Literal[
    "face_swapping",
    "hair_change",
    "clothing_drift",
    "identity_drift",
    "emotion_mismatch",
    "scene_mismatch",
    "age_drift",
    "body_drift",
    "accessory_drift",
]


@dataclass
class IdentityProfile:
    """Full identity lock for one trackable subject."""

    subject_id: str
    subject_kind: SubjectKind
    identity: str
    face: str
    hair: str
    age: str
    body: str
    clothes: str
    accessories: list[str]
    pose: str
    expression: str
    voice: str
    walking_style: str
    skin_tone: str
    eye_color: str
    lighting_adaptation: str
    face_embedding: list[float] = field(default_factory=list)
    face_embedding_ref: str | None = None
    reference_image_urls: list[str] = field(default_factory=list)
    locked_traits: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def lock_prompt(self) -> str:
        accessories = ", ".join(self.accessories) if self.accessories else "none"
        return (
            f"IDENTITY LOCK [{self.subject_id}/{self.subject_kind}]: "
            f"identity={self.identity}; face={self.face}; hair={self.hair}; age={self.age}; "
            f"body={self.body}; clothes={self.clothes}; accessories={accessories}; "
            f"pose={self.pose}; expression={self.expression}; voice={self.voice}; "
            f"walk={self.walking_style}; skin={self.skin_tone}; eyes={self.eye_color}; "
            f"lighting_adapt={self.lighting_adaptation}. "
            f"FORBIDDEN: face swap, hair change, clothing drift, identity drift."
        )


@dataclass
class DriftFinding:
    kind: DriftKind
    severity: float  # 0–1
    subject_id: str
    scene_index: int | None
    shot_index: int | None
    detail: str
    auto_correctable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConsistencyScore:
    overall: float
    identity: float
    face: float
    hair: float
    clothing: float
    body: float
    expression: float
    scene_fit: float
    embedding_stability: float
    details: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationResult:
    passed: bool
    score: ConsistencyScore
    drifts: list[DriftFinding]
    verified_subject_ids: list[str]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score.to_dict(),
            "drifts": [d.to_dict() for d in self.drifts],
            "verified_subject_ids": self.verified_subject_ids,
            "notes": self.notes,
        }


@dataclass
class CorrectionAction:
    target: str  # scene | shot | prompt | character
    index: int | None
    field: str
    before: str
    after: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CharacterConsistencyResult:
    subject_kind: SubjectKind
    profiles: list[IdentityProfile]
    verification: VerificationResult
    corrections: list[CorrectionAction]
    identity_lock_block: str
    embedding_ready: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_kind": self.subject_kind,
            "profiles": [p.to_dict() for p in self.profiles],
            "verification": self.verification.to_dict(),
            "corrections": [c.to_dict() for c in self.corrections],
            "identity_lock_block": self.identity_lock_block,
            "embedding_ready": self.embedding_ready,
            "consistency_score": self.verification.score.to_dict(),
        }

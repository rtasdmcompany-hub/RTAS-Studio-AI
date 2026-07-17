"""Face lock / identity domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ReferenceKind = Literal["uploaded", "generated", "stored"]
LockState = Literal["unlocked", "locking", "locked", "failed"]


PRESERVED_TRAITS = (
    "face_structure",
    "eye_shape",
    "nose",
    "lips",
    "jawline",
    "ears",
    "hairstyle",
    "beard",
    "age",
    "skin_tone",
    "body_proportions",
)


@dataclass
class FaceFeatures:
    face_structure: str
    eye_shape: str
    nose: str
    lips: str
    jawline: str
    ears: str
    hairstyle: str
    beard: str
    age: int
    skin_tone: str
    body_proportions: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def fingerprint(self) -> str:
        import hashlib

        payload = "|".join(
            [
                self.face_structure,
                self.eye_shape,
                self.nose,
                self.lips,
                self.jawline,
                self.ears,
                self.hairstyle,
                self.beard,
                str(self.age),
                self.skin_tone,
                self.body_proportions,
            ]
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:24]


@dataclass
class CharacterReference:
    reference_id: str
    kind: ReferenceKind
    url: str
    character_id: str
    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FaceEmbeddingRecord:
    face_embedding_ref: str
    dimension: int
    vector: list[float]
    regenerated: bool = False
    locked: bool = True

    def to_dict(self) -> dict[str, Any]:
        # Never expose full vector in summaries by default — include ref + meta
        return {
            "face_embedding_ref": self.face_embedding_ref,
            "dimension": self.dimension,
            "locked": self.locked,
            "regenerated": self.regenerated,
            "vector_length": len(self.vector),
        }

    def to_full_dict(self) -> dict[str, Any]:
        return {
            **self.to_dict(),
            "vector": list(self.vector),
        }


@dataclass
class DriftFlag:
    trait: str
    severity: float
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IdentityVerification:
    character_id: str
    identity_score: float
    passed: bool
    drift_detected: bool
    drift_flags: list[DriftFlag] = field(default_factory=list)
    cosine_similarity: float = 1.0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "character_id": self.character_id,
            "identity_score": self.identity_score,
            "passed": self.passed,
            "drift_detected": self.drift_detected,
            "drift_flags": [d.to_dict() for d in self.drift_flags],
            "cosine_similarity": self.cosine_similarity,
            "notes": list(self.notes),
        }


@dataclass
class FaceLockRecord:
    lock_id: str
    character_id: str
    state: LockState
    features: FaceFeatures
    embedding: FaceEmbeddingRecord
    reference: CharacterReference | None
    preserved_traits: list[str] = field(default_factory=lambda: list(PRESERVED_TRAITS))
    identity_strength: float = 0.95
    version: int = 1
    production_ready: bool = True
    last_verification: IdentityVerification | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "lock_id": self.lock_id,
            "character_id": self.character_id,
            "state": self.state,
            "face_embedding_ref": self.embedding.face_embedding_ref,
            "identity_strength": self.identity_strength,
            "version": self.version,
            "production_ready": self.production_ready,
            "preserved_traits": list(self.preserved_traits),
            "reference": self.reference.to_dict() if self.reference else None,
            "features_fingerprint": self.features.fingerprint(),
            "last_identity_score": (
                self.last_verification.identity_score if self.last_verification else None
            ),
            "drift_detected": (
                self.last_verification.drift_detected if self.last_verification else False
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "features": self.features.to_dict(),
            "embedding": self.embedding.to_dict(),
            "last_verification": (
                self.last_verification.to_dict() if self.last_verification else None
            ),
            "metadata": dict(self.metadata),
        }

"""Appearance / outfit / style domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

OutfitCategory = Literal[
    "casual",
    "formal",
    "business",
    "traditional",
    "luxury",
    "sports",
    "custom",
]

StylePresetId = Literal[
    "cinematic",
    "realistic",
    "hyper_realistic",
    "luxury",
    "documentary",
    "commercial",
    "music_video",
    "action",
    "fashion",
]

# Permanently stored appearance profile fields
APPEARANCE_PROFILE_FIELDS = (
    "hairstyle",
    "hair_color",
    "beard_style",
    "eye_color",
    "skin_tone",
    "body_type",
    "height",
    "clothing_style",
    "shoes",
    "accessories",
)

# Must never change when switching outfits
FACIAL_IDENTITY_FIELDS = (
    "eye_color",
    "skin_tone",
    "body_type",
    "height",
    "hairstyle",
    "hair_color",
    "beard_style",
)

# May change with outfit
OUTFIT_MUTABLE_FIELDS = (
    "clothing_style",
    "shoes",
    "accessories",
)


@dataclass
class AppearanceProfile:
    hairstyle: str
    hair_color: str
    beard_style: str
    eye_color: str
    skin_tone: str
    body_type: str
    height: str
    clothing_style: str
    shoes: str
    accessories: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def fingerprint(self) -> str:
        import hashlib

        payload = "|".join(
            [
                self.hairstyle,
                self.hair_color,
                self.beard_style,
                self.eye_color,
                self.skin_tone,
                self.body_type,
                self.height,
                self.clothing_style,
                self.shoes,
                ",".join(sorted(self.accessories)),
            ]
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:24]

    def facial_fingerprint(self) -> str:
        """Identity-safe fingerprint — ignores outfit-mutable fields."""
        import hashlib

        payload = "|".join(
            [
                self.hairstyle,
                self.hair_color,
                self.beard_style,
                self.eye_color,
                self.skin_tone,
                self.body_type,
                self.height,
            ]
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:24]


@dataclass
class OutfitDefinition:
    outfit_id: str
    category: OutfitCategory
    name: str
    clothing_style: str
    shoes: str
    accessories: list[str] = field(default_factory=list)
    description: str = ""
    custom: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StylePreset:
    preset_id: StylePresetId
    name: str
    description: str
    look: dict[str, Any] = field(default_factory=dict)
    lighting: str = "natural"
    color_grade: str = "neutral"
    camera: str = "standard"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AppearanceDriftFlag:
    trait: str
    severity: float
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConsistencyReport:
    character_id: str
    consistent: bool
    appearance_score: float
    drift_detected: bool
    drift_flags: list[AppearanceDriftFlag] = field(default_factory=list)
    face_preserved: bool = True
    body_preserved: bool = True
    hair_preserved: bool = True
    clothing_match: bool = True
    accessories_match: bool = True
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "character_id": self.character_id,
            "consistent": self.consistent,
            "appearance_score": self.appearance_score,
            "drift_detected": self.drift_detected,
            "drift_flags": [d.to_dict() for d in self.drift_flags],
            "face_preserved": self.face_preserved,
            "body_preserved": self.body_preserved,
            "hair_preserved": self.hair_preserved,
            "clothing_match": self.clothing_match,
            "accessories_match": self.accessories_match,
            "notes": list(self.notes),
        }


@dataclass
class AppearanceRecord:
    profile_id: str
    character_id: str
    profile: AppearanceProfile
    active_outfit_id: str | None
    outfits: list[OutfitDefinition] = field(default_factory=list)
    style_preset_id: StylePresetId | None = None
    version: int = 1
    production_ready: bool = True
    last_consistency: ConsistencyReport | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "character_id": self.character_id,
            "active_outfit_id": self.active_outfit_id,
            "style_preset_id": self.style_preset_id,
            "outfit_count": len(self.outfits),
            "version": self.version,
            "production_ready": self.production_ready,
            "appearance_fingerprint": self.profile.fingerprint(),
            "facial_fingerprint": self.profile.facial_fingerprint(),
            "last_appearance_score": (
                self.last_consistency.appearance_score if self.last_consistency else None
            ),
            "drift_detected": (
                self.last_consistency.drift_detected if self.last_consistency else False
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "profile": self.profile.to_dict(),
            "outfits": [o.to_dict() for o in self.outfits],
            "last_consistency": (
                self.last_consistency.to_dict() if self.last_consistency else None
            ),
            "metadata": dict(self.metadata),
        }

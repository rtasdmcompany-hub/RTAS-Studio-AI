"""Character identity, DNA, and job models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

CharacterJobState = Literal[
    "queued",
    "preparing",
    "generating",
    "registering",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]

RegistrySlot = Literal["Character_A", "Character_B", "Character_C"]


@dataclass
class CharacterIdentity:
    unique_id: str
    version: str
    gender: str
    age: int
    ethnicity: str
    body_type: str
    hairstyle: str
    beard: str
    skin: str
    eye_color: str
    clothing: str
    accessories: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CharacterDNA:
    """Persistent character DNA — survives across generations."""

    dna_id: str
    character_id: str
    version: int
    identity: CharacterIdentity
    traits: dict[str, Any] = field(default_factory=dict)
    fingerprint: str = ""
    locked: bool = True
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "dna_id": self.dna_id,
            "character_id": self.character_id,
            "version": self.version,
            "identity": self.identity.to_dict(),
            "traits": dict(self.traits),
            "fingerprint": self.fingerprint,
            "locked": self.locked,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_character_dna_json(self) -> dict[str, Any]:
        """Canonical character_dna.json payload."""
        return {
            "format": "rtas-character-dna-v1",
            "engine_version": self.identity.version,
            **self.to_dict(),
        }


@dataclass
class CharacterTemplate:
    template_id: str
    name: str
    description: str
    defaults: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CharacterMetadata:
    name: str | None
    description: str | None
    tags: list[str]
    template_id: str | None
    registry_slot: str | None
    source_prompt: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CharacterRecord:
    character_id: str
    registry_slot: RegistrySlot | None
    identity: CharacterIdentity
    dna: CharacterDNA
    metadata: CharacterMetadata
    character_version: int
    production_ready: bool = True
    preview_url: str | None = None
    dna_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "character_id": self.character_id,
            "registry_slot": self.registry_slot,
            "identity": self.identity.to_dict(),
            "dna": self.dna.to_character_dna_json(),
            "metadata": self.metadata.to_dict(),
            "character_version": self.character_version,
            "production_ready": self.production_ready,
            "preview_url": self.preview_url,
            "dna_url": self.dna_url,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "character_id": self.character_id,
            "registry_slot": self.registry_slot,
            "unique_id": self.identity.unique_id,
            "version": self.identity.version,
            "gender": self.identity.gender,
            "age": self.identity.age,
            "name": self.metadata.name,
            "character_version": self.character_version,
            "production_ready": self.production_ready,
            "dna_url": self.dna_url,
            "preview_url": self.preview_url,
        }


@dataclass
class CharacterJob:
    job_id: str
    engine: str
    version: str
    state: CharacterJobState
    character: CharacterRecord
    processing_time_ms: float = 0.0
    retry_count: int = 0
    queue_position: int | None = None
    errors: list[str] = field(default_factory=list)
    provider: str = "simulation"
    parent_generation_id: str | None = None
    paddle_verified: bool = False
    history: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "engine": self.engine,
            "version": self.version,
            "state": self.state,
            "character_id": self.character.character_id,
            "registry_slot": self.character.registry_slot,
            "unique_id": self.character.identity.unique_id,
            "character_version": self.character.character_version,
            "production_ready": self.character.production_ready,
            "dna_url": self.character.dna_url,
            "preview_url": self.character.preview_url,
            "processing_time_ms": self.processing_time_ms,
            "retry_count": self.retry_count,
            "queue_position": self.queue_position,
            "paddle_verified": self.paddle_verified,
            "parent_generation_id": self.parent_generation_id,
            "provider": self.provider,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "character": self.character.to_dict(),
            "errors": list(self.errors),
            "history": list(self.history),
            "metadata": dict(self.metadata),
        }

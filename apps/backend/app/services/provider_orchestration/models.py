"""Provider capability and status models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ProviderStatus = Literal["online", "offline", "busy", "disabled", "maintenance"]

Capability = Literal[
    "text",
    "image",
    "video",
    "audio",
    "music",
    "voice",
    "embedding",
    "vision",
    "translation",
]

ALL_CAPABILITIES: tuple[Capability, ...] = (
    "text",
    "image",
    "video",
    "audio",
    "music",
    "voice",
    "embedding",
    "vision",
    "translation",
)

ALL_STATUSES: tuple[ProviderStatus, ...] = (
    "online",
    "offline",
    "busy",
    "disabled",
    "maintenance",
)


@dataclass
class ProviderCapabilityModel:
    """Declared capabilities for a provider."""

    capabilities: list[Capability] = field(default_factory=list)
    models: dict[str, list[str]] = field(default_factory=dict)
    max_concurrency: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderRecord:
    provider_id: str
    display_name: str
    version: str
    status: ProviderStatus
    capabilities: list[Capability]
    priority: int
    configured: bool
    discovered: bool = True
    health_latency_ms: float | None = None
    last_health_at: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

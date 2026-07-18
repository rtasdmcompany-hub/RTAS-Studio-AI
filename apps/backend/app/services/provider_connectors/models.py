"""Standardized request/response, capability, status, and error models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ProviderStatusState = Literal["online", "offline", "busy", "disabled", "maintenance"]

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


@dataclass
class ProviderError:
    code: str
    message: str
    provider: str
    retryable: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StandardRequest:
    """Unified request model across all connectors."""

    prompt: str
    capability: Capability = "text"
    model: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    timeout_sec: float = 30.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StandardResponse:
    """Unified response model across all connectors."""

    provider: str
    success: bool
    capability: Capability
    data: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    provider_version: str | None = None
    error: ProviderError | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "success": self.success,
            "capability": self.capability,
            "data": dict(self.data),
            "latency_ms": self.latency_ms,
            "provider_version": self.provider_version,
            "error": self.error.to_dict() if self.error else None,
            "metadata": dict(self.metadata),
        }


@dataclass
class ProviderInfo:
    provider_id: str
    display_name: str
    version: str
    status: ProviderStatusState
    capabilities: list[Capability]
    configured: bool
    priority: int = 100
    latency_ms: float | None = None
    last_health_at: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

"""Model Registry — catalog of provider models with priority metrics."""

from __future__ import annotations

from typing import Any

from app.services.model_routing.models import ALL_REQUEST_TYPES, ModelEntry, RequestType

_DEFAULT_MODELS: list[ModelEntry] = [
    ModelEntry("gpt-4o", "openai", ["text", "chat", "code", "vision", "translation"], priority=10, cost_per_1k=0.005, latency_ms=350, quality_score=0.94, load=0.25),
    ModelEntry("gpt-4o-mini", "openai", ["text", "chat", "code", "translation"], priority=20, cost_per_1k=0.001, latency_ms=220, quality_score=0.88, load=0.15),
    ModelEntry("claude-3-5-sonnet", "claude", ["text", "chat", "code", "vision"], priority=15, cost_per_1k=0.006, latency_ms=380, quality_score=0.93, load=0.3),
    ModelEntry("gemini-1.5-pro", "gemini", ["text", "chat", "vision", "translation"], priority=25, cost_per_1k=0.003, latency_ms=400, quality_score=0.9, load=0.2),
    ModelEntry("sdxl", "stability", ["image"], priority=10, cost_per_1k=0.02, latency_ms=900, quality_score=0.91, load=0.35),
    ModelEntry("dall-e-3", "openai", ["image"], priority=20, cost_per_1k=0.04, latency_ms=1200, quality_score=0.92, load=0.4),
    ModelEntry("flux-dev", "fal", ["image", "video"], priority=30, cost_per_1k=0.015, latency_ms=800, quality_score=0.89, load=0.28),
    ModelEntry("runpod-video-xl", "runpod", ["video"], priority=10, cost_per_1k=0.05, latency_ms=2500, quality_score=0.9, load=0.45),
    ModelEntry("fal-video", "fal", ["video"], priority=20, cost_per_1k=0.04, latency_ms=2200, quality_score=0.88, load=0.35),
    ModelEntry("replicate-svd", "replicate", ["video", "image"], priority=35, cost_per_1k=0.035, latency_ms=2800, quality_score=0.86, load=0.3),
    ModelEntry("eleven-multilingual-v2", "elevenlabs", ["voice", "audio"], priority=10, cost_per_1k=0.018, latency_ms=500, quality_score=0.95, load=0.22),
    ModelEntry("eleven-music", "elevenlabs", ["music", "audio"], priority=15, cost_per_1k=0.025, latency_ms=1500, quality_score=0.9, load=0.25),
    ModelEntry("whisper-1", "openai", ["audio", "translation"], priority=40, cost_per_1k=0.006, latency_ms=600, quality_score=0.87, load=0.18),
    ModelEntry(
        "rtas-sim-universal",
        "simulation",
        list(ALL_REQUEST_TYPES),
        priority=100,
        cost_per_1k=0.0,
        latency_ms=50,
        quality_score=0.7,
        load=0.05,
    ),
]


class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, ModelEntry] = {}
        for m in _DEFAULT_MODELS:
            self.register(m)

    def register(self, entry: ModelEntry) -> None:
        if not entry.model_id:
            raise ValueError("model_id is required")
        self._models[entry.model_id] = entry

    def get(self, model_id: str) -> ModelEntry | None:
        return self._models.get(model_id)

    def all(self) -> list[ModelEntry]:
        return sorted(self._models.values(), key=lambda m: (m.priority, m.model_id))

    def for_type(self, request_type: RequestType) -> list[ModelEntry]:
        return [m for m in self.all() if m.enabled and request_type in m.request_types]

    def for_provider(self, provider_id: str, request_type: RequestType | None = None) -> list[ModelEntry]:
        rows = [m for m in self.all() if m.enabled and m.provider_id == provider_id]
        if request_type:
            rows = [m for m in rows if request_type in m.request_types]
        return sorted(rows, key=lambda m: m.priority)

    def list_payload(self) -> dict[str, Any]:
        models = [m.to_dict() for m in self.all()]
        return {
            "models": models,
            "count": len(models),
            "providers": sorted({m.provider_id for m in self.all()}),
        }


_registry: ModelRegistry | None = None


def get_model_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


def reset_model_registry() -> None:
    global _registry
    _registry = None

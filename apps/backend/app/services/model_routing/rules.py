"""Routing rules — preferred providers per request type."""

from __future__ import annotations

from app.services.model_routing.models import RequestType

# Preferred provider order per request type (primary → fallbacks)
ROUTING_RULES: dict[RequestType, tuple[str, ...]] = {
    "text": ("openai", "claude", "gemini", "simulation"),
    "chat": ("openai", "claude", "gemini", "simulation"),
    "code": ("openai", "claude", "gemini", "simulation"),
    "image": ("stability", "openai", "fal", "replicate", "simulation"),
    "video": ("runpod", "fal", "replicate", "simulation"),
    "audio": ("elevenlabs", "openai", "fal", "simulation"),
    "music": ("elevenlabs", "fal", "simulation"),
    "voice": ("elevenlabs", "openai", "simulation"),
    "vision": ("openai", "gemini", "claude", "simulation"),
    "translation": ("openai", "gemini", "claude", "simulation"),
}


def preferred_providers(request_type: RequestType) -> list[str]:
    return list(ROUTING_RULES.get(request_type, ("simulation",)))


def list_rules() -> dict[str, list[str]]:
    return {k: list(v) for k, v in ROUTING_RULES.items()}

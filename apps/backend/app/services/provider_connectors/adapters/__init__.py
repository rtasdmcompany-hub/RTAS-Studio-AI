"""Built-in provider adapters for Phase 6 Sprint 2."""

from app.services.provider_connectors.adapters.claude_adapter import ClaudeConnector
from app.services.provider_connectors.adapters.elevenlabs_adapter import ElevenLabsConnector
from app.services.provider_connectors.adapters.gemini_adapter import GeminiConnector
from app.services.provider_connectors.adapters.openai_adapter import OpenAIConnector
from app.services.provider_connectors.adapters.runpod_adapter import RunPodConnector
from app.services.provider_connectors.adapters.stability_adapter import StabilityConnector

BUILTIN_CONNECTORS = (
    OpenAIConnector,
    GeminiConnector,
    ClaudeConnector,
    RunPodConnector,
    StabilityConnector,
    ElevenLabsConnector,
)

__all__ = [
    "OpenAIConnector",
    "GeminiConnector",
    "ClaudeConnector",
    "RunPodConnector",
    "StabilityConnector",
    "ElevenLabsConnector",
    "BUILTIN_CONNECTORS",
]

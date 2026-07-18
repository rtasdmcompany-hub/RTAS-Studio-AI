"""Built-in provider stubs for automatic discovery (unified interface)."""

from __future__ import annotations

from typing import Any

from app.services.provider_orchestration.base import BaseProviderInterface
from app.services.provider_orchestration.models import Capability


class _StubProvider(BaseProviderInterface):
    """Lightweight discovered provider — placeholder invoke until live keys wired."""

    def __init__(
        self,
        provider_id: str,
        display_name: str,
        capabilities: tuple[Capability, ...],
        priority: int,
        *,
        version: str = "1.0.0",
        env_key_hints: tuple[str, ...] = (),
    ):
        self.provider_id = provider_id
        self.display_name = display_name
        self.capabilities = capabilities
        self.version = version
        self.default_priority = priority
        self._env_key_hints = env_key_hints
        super().__init__()
        self.set_priority(priority)
        self._detect_configuration()

    def _detect_configuration(self) -> None:
        import os

        configured = False
        for key in self._env_key_hints:
            if (os.environ.get(key) or "").strip():
                configured = True
                break
        self.set_configured(configured)
        # Always online when enabled for orchestration foundation (simulation-safe)
        if self._enabled:
            self.set_status("online")

    async def invoke(
        self,
        prompt: str,
        *,
        capability: Capability = "text",
        **kwargs: Any,
    ) -> dict[str, Any]:
        if not self.supports(capability):
            return {
                "success": False,
                "provider": self.provider_id,
                "error": f"unsupported_capability:{capability}",
            }
        return {
            "success": True,
            "provider": self.provider_id,
            "capability": capability,
            "mode": "orchestration_stub" if not self.is_configured() else "configured",
            "prompt_echo": (prompt or "")[:160],
            "version": self.version,
        }


def builtin_provider_factories() -> list[type]:
    """Return factory callables that construct builtin providers."""
    return [
        lambda: _StubProvider(
            "fal",
            "Fal.ai",
            ("image", "video", "audio"),
            15,
            env_key_hints=("FAL_KEY", "FAL_API_KEY"),
        ),
        lambda: _StubProvider(
            "openai",
            "OpenAI",
            ("text", "image", "audio", "voice", "embedding", "vision", "translation"),
            20,
            env_key_hints=("OPENAI_API_KEY",),
        ),
        lambda: _StubProvider(
            "gemini",
            "Google Gemini",
            ("text", "image", "vision", "embedding", "translation"),
            25,
            env_key_hints=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        ),
        lambda: _StubProvider(
            "claude",
            "Anthropic Claude",
            ("text", "vision"),
            30,
            env_key_hints=("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"),
        ),
        lambda: _StubProvider(
            "replicate",
            "Replicate",
            ("image", "video", "audio"),
            35,
            env_key_hints=("REPLICATE_API_TOKEN", "REPLICATE_API_KEY"),
        ),
        lambda: _StubProvider(
            "stability",
            "Stability AI",
            ("image", "video"),
            40,
            env_key_hints=("STABILITY_API_KEY",),
        ),
        lambda: _StubProvider(
            "elevenlabs",
            "ElevenLabs",
            ("voice", "audio", "music"),
            45,
            env_key_hints=("ELEVENLABS_API_KEY",),
        ),
        lambda: _StubProvider(
            "runpod",
            "RunPod",
            ("image", "video", "text"),
            50,
            env_key_hints=("RUNPOD_API_KEY",),
        ),
        lambda: _StubProvider(
            "simulation",
            "RTAS Simulation",
            (
                "text",
                "image",
                "video",
                "audio",
                "music",
                "voice",
                "embedding",
                "vision",
                "translation",
            ),
            100,
        ),
    ]

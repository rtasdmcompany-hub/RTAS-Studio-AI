"""Provider registry — detect and list all Multi-AI adapters."""

from __future__ import annotations

from app.services.providers.base import BaseAIProvider
from app.services.providers.comfyui import ComfyUIProvider
from app.services.providers.diffusers_local import DiffusersInstantIDProvider
from app.services.providers.fal import FalProvider
from app.services.providers.replicate import ReplicateProvider
from app.services.providers.specialty import (
    CogVideoProvider,
    GoogleVeoProvider,
    HailuoProvider,
    KlingProvider,
    LumaProvider,
    PikaProvider,
    RunwayProvider,
    StableVideoDiffusionProvider,
)

# Preferred failover order for auto mode (live cloud first).
DEFAULT_FAILOVER_ORDER: tuple[str, ...] = (
    "fal",
    "kling",
    "luma",
    "veo",
    "runway",
    "hailuo",
    "pika",
    "replicate",
    "svd",
    "cogvideo",
    "diffusers",
    "comfyui",
)


def build_provider_registry() -> dict[str, BaseAIProvider]:
    return {
        "fal": FalProvider(),
        "replicate": ReplicateProvider(),
        "veo": GoogleVeoProvider(),
        "runway": RunwayProvider(),
        "kling": KlingProvider(),
        "hailuo": HailuoProvider(),
        "pika": PikaProvider(),
        "luma": LumaProvider(),
        "svd": StableVideoDiffusionProvider(),
        "cogvideo": CogVideoProvider(),
        "comfyui": ComfyUIProvider(),
        "diffusers": DiffusersInstantIDProvider(),
    }


def detect_available_providers(
    registry: dict[str, BaseAIProvider] | None = None,
) -> list[str]:
    adapters = registry or build_provider_registry()
    return [name for name, adapter in adapters.items() if adapter.is_configured()]


def provider_compatibility_matrix(
    registry: dict[str, BaseAIProvider] | None = None,
) -> list[dict]:
    adapters = registry or build_provider_registry()
    rows = []
    for name, adapter in adapters.items():
        cap = adapter.capability()
        rows.append(
            {
                "provider": name,
                "display_name": cap.display_name,
                "configured": adapter.is_configured(),
                "strengths": cap.strengths,
                "max_duration_seconds": cap.max_duration_seconds,
                "fal_model": cap.fal_model,
                "cost_per_second_usd": adapter.cost_per_second_usd,
            }
        )
    return rows

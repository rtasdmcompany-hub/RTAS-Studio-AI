"""Catalogs for RC-1 modules, AI flows, providers, and regression phases."""

from __future__ import annotations

from typing import Final

AI_GENERATION_FLOWS: Final[tuple[str, ...]] = (
    "prompt_to_video",
    "prompt_to_image",
    "image_to_video",
    "text_to_audio",
    "ai_routing",
    "model_selection",
    "queue_processing",
    "gpu_processing",
    "export_pipeline",
)

E2E_WORKFLOW_STEPS: Final[tuple[str, ...]] = (
    "user_registration",
    "authentication",
    "organization",
    "workspace",
    "project",
    "asset_upload",
    "prompt_submission",
    "ai_generation",
    "rendering",
    "storage",
    "billing",
    "export",
    "download",
)

RC1_MODULES: Final[tuple[str, ...]] = (
    "core_features",
    "marketplace",
    "billing",
    "credits",
    "ai_agents",
    "automation",
    "public_apis",
    "plugins",
    "developer_portal",
    "analytics",
)

REQUIRED_PROVIDERS: Final[tuple[str, ...]] = (
    "fal",
    "runpod",
    "openai",
    "gemini",
    "claude",
)

REGRESSION_PHASES: Final[tuple[int, ...]] = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)

QUALITY_DIMENSIONS: Final[tuple[str, ...]] = (
    "image_quality",
    "video_quality",
    "audio_quality",
    "rendering_accuracy",
    "prompt_accuracy",
    "export_integrity",
    "download_integrity",
)

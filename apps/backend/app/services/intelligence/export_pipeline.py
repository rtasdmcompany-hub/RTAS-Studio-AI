"""Export Pipeline planner — delivery package metadata (no UI)."""

from __future__ import annotations

from app.services.intelligence.models import ExportPlan, PromptIntelligenceResult


def plan_export(intelligence: PromptIntelligenceResult) -> ExportPlan:
    resolution = "1080p" if intelligence.estimated_duration_seconds <= 30 else "1080p"
    return ExportPlan(
        format="mp4",
        resolution=resolution,
        container="h264",
        audio_mix="stereo_normalized",
        delivery_notes=[
            "Preserve original aspect unless client overrides",
            "Attach generation job id in delivery metadata",
            f"Target duration ~{intelligence.estimated_duration_seconds}s",
        ],
    )

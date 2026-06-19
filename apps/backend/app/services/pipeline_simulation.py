"""Mirrors frontend `generation-simulation.ts` stage sequence."""

from app.schemas.generation import GenerateRequest, ProcessingStep

STAGES: list[tuple[int, int, str]] = [
    (0, 20, "Initializing RTAS AI Engine & parsing assets…"),
    (21, 50, "Syncing facial features via Instant-ID pipeline…"),
    (51, 80, "Generating high-fidelity cinematic video frames…"),
    (81, 100, "Finalizing video compilation and rendering preview…"),
]

ALT_STAGE_2 = "Applying style embeddings & scene composition…"

# Same path as apps/web/public/video/preview-showcase.mp4 (Next.js serves /video/*).
SIMULATION_PREVIEW_VIDEO = "/video/preview-showcase.mp4"

# Cinematic remote fallback if the public showcase is missing from the frontend build.
REMOTE_PREVIEW_FALLBACK = (
    "https://videos.pexels.com/video-files/4058822/4058822-uhd_2560_1440_25fps.mp4"
)
# Frontend maps /video/preview-showcase.mp4 → PRIMARY_SHOWCASE_STREAM_URL when uncached.

# Legacy alias — simulation always prefers the local public sample path.
PREVIEW_PLACEHOLDER_VIDEO = SIMULATION_PREVIEW_VIDEO

CREDITS_PER_SECOND = 1
FREE_TRIAL_MAX_SECONDS = 20


def select_provider(body: GenerateRequest) -> str:
    if body.visual_style == "real" and body.identity_pipeline.instant_id_enabled:
        return "instant-id"
    if body.visual_style == "real" and body.identity_pipeline.ip_adapter_enabled:
        return "ip-adapter"
    if body.visual_style == "real":
        return "kling-character-id"
    if body.visual_style == "avatar":
        return "runway-gen4"
    if body.visual_style == "cartoon":
        return "fal-cartoon"
    return "replicate-default"


def credits_for_duration(seconds: int) -> int:
    return max(1, round(seconds * CREDITS_PER_SECOND))


def build_processing_steps(body: GenerateRequest) -> list[ProcessingStep]:
    use_instant_id = body.visual_style == "real"
    steps: list[ProcessingStep] = []

    for i, (min_p, max_p, label) in enumerate(STAGES):
        stage_label = ALT_STAGE_2 if i == 1 and not use_instant_id else label
        substeps = 12
        for s in range(substeps + 1):
            t = s / substeps
            percent = min(100, round(min_p + t * (max_p - min_p)))
            steps.append(
                ProcessingStep(
                    percent=percent,
                    message=stage_label,
                    stage_index=i,
                )
            )

    steps.append(
        ProcessingStep(
            percent=100,
            message="Complete — loading preview…",
            stage_index=len(STAGES) - 1,
        )
    )
    return steps


def resolve_output_flags(body: GenerateRequest) -> tuple[bool, bool, int, int]:
    """preview_only, can_download, credits_used, effective_duration"""
    preview = body.preview_only
    duration = body.duration_seconds

    if body.use_free_trial:
        duration = min(duration, FREE_TRIAL_MAX_SECONDS)
        return False, False, 0, duration

    profile = body.profile
    needed = credits_for_duration(duration)

    if preview:
        return True, False, 0, duration

    if profile and profile.subscription_active and profile.credits >= needed:
        return False, True, needed, duration

    return True, False, 0, duration

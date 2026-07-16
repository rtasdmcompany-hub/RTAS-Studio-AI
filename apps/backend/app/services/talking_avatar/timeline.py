"""Compose full Talking Avatar timeline."""

from __future__ import annotations

from typing import Any

from app.services.talking_avatar.lip_sync import build_lip_sync_frames
from app.services.talking_avatar.models import AvatarTimeline
from app.services.talking_avatar.motion import (
    build_expressions_and_smiles,
    build_eye_contact_and_blinks,
    build_head_motion,
    build_idle_motion,
)


def estimate_runtime(
    *,
    duration_hint: float | None,
    audio_director: dict[str, Any] | None,
    timeline: dict[str, Any] | None,
) -> float:
    if duration_hint and duration_hint > 0:
        return float(duration_hint)
    if audio_director and audio_director.get("estimated_runtime_seconds"):
        return float(audio_director["estimated_runtime_seconds"])
    if timeline and timeline.get("total_duration_seconds"):
        return float(timeline["total_duration_seconds"])
    return 12.0


def build_avatar_timeline(
    *,
    runtime_seconds: float,
    character_id: str,
    emotion: str,
    audio_director: dict[str, Any] | None,
    dialogue: str | None,
    natural_motion: bool = True,
) -> AvatarTimeline:
    runtime = max(2.0, float(runtime_seconds))
    lip = build_lip_sync_frames(
        audio_director=audio_director,
        character_id=character_id,
        dialogue=dialogue,
        runtime_seconds=runtime,
    )
    head = build_head_motion(runtime, emotion=emotion, natural_motion=natural_motion)
    eyes, blinks = build_eye_contact_and_blinks(runtime, natural_motion=natural_motion)
    expressions, smiles = build_expressions_and_smiles(
        runtime, emotion=emotion, lip_sync=lip
    )
    idle = build_idle_motion(runtime, natural_motion=natural_motion)
    return AvatarTimeline(
        runtime_seconds=round(runtime, 2),
        lip_sync=lip,
        head_motion=head,
        eye_contact=eyes,
        expressions=expressions,
        idle_motion=idle,
        blinks=blinks,
        smiles=smiles,
    )

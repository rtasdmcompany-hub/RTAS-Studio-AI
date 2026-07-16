"""Natural human animation constraints and directives."""

from __future__ import annotations

from typing import Any

from app.services.motion_intelligence.models import (
    LocomotionKind,
    NaturalAnimationHint,
    SceneMotionPlan,
)


def build_natural_hint(
    *,
    primary_kinds: list[LocomotionKind],
    emotion: str | None = None,
) -> NaturalAnimationHint:
    emo = (emotion or "").lower()
    breath = 4.0
    if emo in ("excited", "angry", "intense"):
        breath = 3.2
    elif emo in ("sad", "calm", "lonely"):
        breath = 5.0

    notes = [
        "Ease in/out all major pose changes — no hard cuts on body.",
        "Keep micro-movements alive during holds (breath, blink-adjacent head).",
        "Secondary motion: hair, cloth, arms follow primary locomotion.",
    ]
    if any(k in ("walking", "running") for k in primary_kinds):
        notes.append("Lock foot contact; avoid sliding feet on ground plane.")
        notes.append("Hip leads locomotion; shoulders counter-rotate lightly.")
    if "sitting" in primary_kinds:
        notes.append("Sit with controlled descent; settle weight into seat.")
    if "turning" in primary_kinds:
        notes.append("Eyes/head lead turn slightly before torso.")

    return NaturalAnimationHint(
        ease_in_out=True,
        avoid_robotic=True,
        micro_movements=True,
        breath_cycle_sec=breath,
        weight_transfer=True,
        secondary_motion=True,
        foot_contact_lock=any(k in ("walking", "running") for k in primary_kinds),
        head_follows_gaze=True,
        notes=notes,
    )


def build_animation_directives(
    scenes: list[SceneMotionPlan],
    natural: NaturalAnimationHint,
    *,
    walking_styles: dict[str, str] | None = None,
) -> list[str]:
    directives: list[str] = [
        "NATURAL HUMAN ANIMATION: organic timing, no robotic holds.",
        f"Breath cycle ~{natural.breath_cycle_sec:.1f}s; micro-movements={natural.micro_movements}.",
    ]
    for note in natural.notes[:6]:
        directives.append(note)

    for style in (walking_styles or {}).values():
        if style:
            directives.append(f"Preserve walking style: {style}")

    for scene in scenes[:8]:
        directives.append(
            f"Scene {scene.scene_index}: primary={scene.primary_locomotion}; "
            f"loco={len(scene.locomotion)} gaze={len(scene.gaze)} "
            f"hands={len(scene.hand_motion)} body={len(scene.body_motion)}"
        )
        for n in scene.director_notes[:2]:
            directives.append(f"  director: {n}")

    # Deduplicate while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for d in directives:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


def flatten_timeline(scenes: list[SceneMotionPlan]) -> list[dict[str, Any]]:
    """Global timeline sorted by absolute time (scene-local for now)."""
    events: list[dict[str, Any]] = []
    offset = 0.0
    for scene in scenes:
        for c in scene.locomotion:
            events.append(
                {
                    "t": round(offset + c.start_sec, 3),
                    "end": round(offset + c.end_sec, 3),
                    "channel": "locomotion",
                    "kind": c.kind,
                    "scene": scene.scene_index,
                    "character_id": c.character_id,
                    "intensity": c.intensity,
                    "direction": c.direction,
                }
            )
        for c in scene.gaze:
            events.append(
                {
                    "t": round(offset + c.start_sec, 3),
                    "end": round(offset + c.end_sec, 3),
                    "channel": "gaze",
                    "kind": "looking",
                    "target": c.target,
                    "scene": scene.scene_index,
                    "character_id": c.character_id,
                }
            )
        for c in scene.hand_motion:
            events.append(
                {
                    "t": round(offset + c.start_sec, 3),
                    "end": round(offset + c.end_sec, 3),
                    "channel": "hand",
                    "kind": c.kind,
                    "side": c.side,
                    "scene": scene.scene_index,
                    "character_id": c.character_id,
                }
            )
        for c in scene.body_motion:
            events.append(
                {
                    "t": round(offset + c.start_sec, 3),
                    "end": round(offset + c.end_sec, 3),
                    "channel": "body",
                    "kind": c.kind,
                    "scene": scene.scene_index,
                    "character_id": c.character_id,
                }
            )
        offset += float(scene.duration_seconds or 0)
    events.sort(key=lambda e: (e["t"], e["channel"]))
    return events

"""Generate professional camera motion keyframes and cues."""

from __future__ import annotations

import math
from typing import Any

from app.services.camera_motion.catalog import display, spec
from app.services.camera_motion.models import (
    CameraKeyframe,
    CameraMotionCue,
    CameraMotionKind,
)


def _intensity_from_pacing(pacing: str | None, base: float = 0.55) -> float:
    p = (pacing or "").lower()
    if any(x in p for x in ("fast", "urgent", "intense")):
        return min(1.0, base + 0.25)
    if any(x in p for x in ("slow", "gentle", "intimate")):
        return max(0.2, base - 0.2)
    return base


def _direction_for(kind: CameraMotionKind, text: str) -> str:
    t = (text or "").lower()
    if kind == "crane":
        return "down" if any(x in t for x in ("descend", "down", "land")) else "up"
    if kind == "pull_out":
        return "back"
    if kind in ("push_in", "dolly"):
        return "forward"
    if kind == "slider":
        return "left" if "left" in t else "right"
    if kind == "orbit":
        return "around"
    if kind in ("tracking", "steadicam"):
        return "follow"
    if kind == "drone":
        return "down" if "descend" in t else "forward"
    return "forward"


def build_keyframes(
    kind: CameraMotionKind,
    *,
    intensity: float,
    direction: str,
) -> list[CameraKeyframe]:
    """Relative path: subject at origin; camera starts ~z=2.5."""
    amp = 0.4 + 0.9 * intensity
    fov0 = 40.0
    fov1 = 40.0

    if kind in ("push_in", "dolly") and direction != "back":
        start = (0.0, 1.5, 3.0)
        end = (0.0, 1.5, max(0.9, 3.0 - amp * 1.4))
        fov1 = 36.0 if kind == "push_in" else 38.0
    elif kind == "pull_out" or (kind == "dolly" and direction == "back"):
        start = (0.0, 1.5, 1.6)
        end = (0.0, 1.5, 1.6 + amp * 1.6)
        fov1 = 48.0
    elif kind == "crane":
        if direction == "down":
            start = (0.0, 1.5 + amp * 2.2, 3.2)
            end = (0.0, 1.5, 2.4)
        else:
            start = (0.0, 1.2, 2.6)
            end = (0.0, 1.2 + amp * 2.0, 3.4)
        fov0, fov1 = 32.0, 40.0
    elif kind == "drone":
        start = (0.0, 4.0 + amp, 6.0)
        end = (amp * 0.5, 2.5, 3.5)
        fov0, fov1 = 28.0, 35.0
    elif kind == "orbit":
        # Sample arc
        keys: list[CameraKeyframe] = []
        radius = 2.4
        yaw0 = -0.55 * amp
        for i, t in enumerate((0.0, 0.5, 1.0)):
            yaw = yaw0 + t * 1.1 * amp
            x = math.sin(yaw) * radius
            z = math.cos(yaw) * radius
            keys.append(
                CameraKeyframe(
                    t=t,
                    position=(round(x, 3), 1.5, round(z, 3)),
                    look_at=(0.0, 1.4, 0.0),
                    fov_deg=42.0,
                )
            )
        return keys
    elif kind == "slider":
        sign = -1.0 if direction == "left" else 1.0
        start = (sign * -amp * 0.8, 1.5, 2.4)
        end = (sign * amp * 0.8, 1.5, 2.4)
    elif kind in ("tracking", "steadicam"):
        start = (-0.3, 1.5, 2.2)
        end = (0.3 + amp * 0.4, 1.5, 2.0)
        fov1 = 38.0
    elif kind == "pov":
        start = (0.0, 1.6, 0.05)
        end = (0.05 * amp, 1.6, 0.4)
        fov0, fov1 = 55.0, 50.0
    elif kind == "handheld":
        start = (0.05, 1.45, 2.3)
        end = (-0.05, 1.55, 2.1)
        fov0, fov1 = 40.0, 39.0
    else:  # static
        start = (0.0, 1.5, 2.5)
        end = start
        return [
            CameraKeyframe(0.0, start, (0.0, 1.4, 0.0), fov0),
            CameraKeyframe(1.0, end, (0.0, 1.4, 0.0), fov0),
        ]

    mid = (
        round((start[0] + end[0]) / 2, 3),
        round((start[1] + end[1]) / 2, 3),
        round((start[2] + end[2]) / 2, 3),
    )
    look = (0.0, 1.4, 0.0) if kind != "pov" else (0.0, 1.5, 2.0)
    return [
        CameraKeyframe(0.0, start, look, fov0),
        CameraKeyframe(0.5, mid, look, (fov0 + fov1) / 2),
        CameraKeyframe(1.0, end, look, fov1),
    ]


def plan_motion_cues(
    kind: CameraMotionKind,
    *,
    duration_seconds: float,
    text: str,
    scene_index: int,
    pacing: str | None = None,
    framing: str | None = None,
    shot_index: int | None = None,
) -> list[CameraMotionCue]:
    dur = max(1.0, float(duration_seconds or 4.0))
    s = spec(kind)
    intensity = _intensity_from_pacing(pacing, base=0.55)
    direction = _direction_for(kind, text)
    speed = round(min(1.0, 0.35 + intensity * 0.55), 3)
    if kind in ("drone", "crane"):
        speed = round(min(1.0, speed * 0.85), 3)
    if kind == "handheld":
        speed = round(min(1.0, speed * 1.1), 3)

    # Intro settle → primary move → optional settle
    cues: list[CameraMotionCue] = []
    primary_start = 0.0
    primary_end = dur

    if dur > 3.5 and kind not in ("static", "pov"):
        settle = min(0.45, dur * 0.1)
        cues.append(
            CameraMotionCue(
                start_sec=0.0,
                end_sec=round(settle, 3),
                kind="static",
                intensity=0.2,
                speed=0.05,
                ease="linear",
                direction="forward",
                subject_lock=True,
                shake=0.0,
                keyframes=build_keyframes("static", intensity=0.2, direction="forward"),
                lens_hint=s["lens_hint"],
                notes="pre-roll settle",
                scene_index=scene_index,
                shot_index=shot_index,
            )
        )
        primary_start = settle
        if kind in ("push_in", "orbit", "dolly") and dur > 5:
            primary_end = dur * 0.85

    keys = build_keyframes(kind, intensity=intensity, direction=direction)
    notes = f"{display(kind)} — {s['description']}"
    if framing:
        notes += f"; framing={framing}"

    cues.append(
        CameraMotionCue(
            start_sec=round(primary_start, 3),
            end_sec=round(primary_end, 3),
            kind=kind,
            intensity=round(intensity, 3),
            speed=speed,
            ease=str(s["ease"]),
            direction=direction,
            subject_lock=bool(s["subject_lock"]),
            shake=float(s["shake"]),
            keyframes=keys,
            lens_hint=str(s["lens_hint"]),
            notes=notes,
            scene_index=scene_index,
            shot_index=shot_index,
        )
    )

    if primary_end < dur - 0.15:
        cues.append(
            CameraMotionCue(
                start_sec=round(primary_end, 3),
                end_sec=round(dur, 3),
                kind="static" if kind != "handheld" else "handheld",
                intensity=0.25 if kind != "handheld" else intensity * 0.6,
                speed=0.08,
                ease="ease_out",
                direction=direction,
                subject_lock=True,
                shake=float(s["shake"]) * 0.5,
                keyframes=build_keyframes(
                    "static" if kind != "handheld" else "handheld",
                    intensity=0.25,
                    direction=direction,
                ),
                lens_hint=s["lens_hint"],
                notes="hold / breathe",
                scene_index=scene_index,
                shot_index=shot_index,
            )
        )

    return cues


def flatten_timeline(scenes: list[Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    offset = 0.0
    for scene in scenes:
        for cue in scene.cues:
            events.append(
                {
                    "t": round(offset + cue.start_sec, 3),
                    "end": round(offset + cue.end_sec, 3),
                    "kind": cue.kind,
                    "display": display(cue.kind),
                    "scene": scene.scene_index,
                    "intensity": cue.intensity,
                    "speed": cue.speed,
                    "direction": cue.direction,
                    "shake": cue.shake,
                    "lens_hint": cue.lens_hint,
                }
            )
        offset += float(scene.duration_seconds or 0)
    events.sort(key=lambda e: (e["t"], e["kind"]))
    return events

"""Locomotion detection and cue planning: walk, run, sit, stand, turn."""

from __future__ import annotations

import re
from typing import Any

from app.services.motion_intelligence.models import LocomotionCue, LocomotionKind

_PATTERNS: list[tuple[LocomotionKind, re.Pattern[str], float]] = [
    ("running", re.compile(r"\b(runs?|running|sprint(?:ing)?|dash(?:ing)?|jogs?|jogging)\b", re.I), 0.9),
    ("walking", re.compile(r"\b(walks?|walking|strolls?|strides?|paces?)\b", re.I), 0.7),
    ("sitting", re.compile(r"\b(sits?|sitting|seated|sit down)\b", re.I), 0.65),
    ("standing", re.compile(r"\b(stands?|standing|stands up|get up|upright)\b", re.I), 0.55),
    ("turning", re.compile(r"\b(turns?|turning|spins?|pivots?|looks? around|whirls?)\b", re.I), 0.6),
    ("looking", re.compile(r"\b(looks?|looking|gazes?|stares?|watches?|glances?)\b", re.I), 0.5),
]


def detect_primary_locomotion(
    text: str,
    *,
    actions: list[str] | None = None,
) -> LocomotionKind:
    blob = " ".join([text or "", " ".join(actions or [])]).strip().lower()
    if not blob:
        return "standing"

    best: LocomotionKind = "standing"
    best_score = 0.0
    for kind, pat, weight in _PATTERNS:
        if pat.search(blob):
            # Prefer more energetic / specific matches
            score = weight + (0.05 if kind in ("running", "walking") else 0.0)
            if score > best_score:
                best_score = score
                best = kind
    return best


def _direction_from_text(text: str) -> str:
    t = (text or "").lower()
    if any(w in t for w in ("toward camera", "to camera", "look at camera", "into camera")):
        return "toward_camera"
    if any(w in t for w in ("away", "leave", "exit", "depart")):
        return "away"
    if any(w in t for w in ("left", "stage left")):
        return "left"
    if any(w in t for w in ("right", "stage right")):
        return "right"
    if any(w in t for w in ("back", "behind", "retreat")):
        return "back"
    return "forward"


def _speed_for(kind: LocomotionKind, intensity: float) -> float:
    base = {
        "running": 0.85,
        "walking": 0.45,
        "turning": 0.35,
        "looking": 0.15,
        "sitting": 0.1,
        "standing": 0.05,
        "idle": 0.05,
    }.get(kind, 0.2)
    return round(min(1.0, max(0.05, base * (0.7 + 0.6 * intensity))), 3)


def plan_locomotion_cues(
    *,
    duration_seconds: float,
    primary: LocomotionKind,
    text: str,
    character_id: str | None,
    walking_style: str | None = None,
    pacing: str | None = None,
) -> list[LocomotionCue]:
    """Build a natural locomotion arc for one scene."""
    dur = max(1.0, float(duration_seconds or 4.0))
    direction = _direction_from_text(text)
    intensity = 0.55
    if pacing and any(x in pacing.lower() for x in ("fast", "intense", "urgent")):
        intensity = 0.8
    elif pacing and any(x in pacing.lower() for x in ("slow", "calm", "gentle")):
        intensity = 0.35

    style_note = (walking_style or "").strip()
    cues: list[LocomotionCue] = []

    if primary == "running":
        # Accel → run → ease
        a = min(dur * 0.15, 0.8)
        b = max(a + 0.5, dur * 0.85)
        cues.append(
            LocomotionCue(0.0, round(a, 3), "standing", 0.3, direction, 0.1, character_id, "prep")
        )
        cues.append(
            LocomotionCue(
                round(a, 3),
                round(b, 3),
                "running",
                intensity,
                direction,
                _speed_for("running", intensity),
                character_id,
                style_note or "athletic run",
            )
        )
        if b < dur:
            cues.append(
                LocomotionCue(
                    round(b, 3),
                    round(dur, 3),
                    "walking",
                    0.4,
                    direction,
                    _speed_for("walking", 0.4),
                    character_id,
                    "decelerate",
                )
            )
    elif primary == "walking":
        a = min(0.4, dur * 0.1)
        cues.append(
            LocomotionCue(0.0, round(a, 3), "standing", 0.25, direction, 0.08, character_id, "start")
        )
        cues.append(
            LocomotionCue(
                round(a, 3),
                round(dur, 3),
                "walking",
                intensity,
                direction,
                _speed_for("walking", intensity),
                character_id,
                style_note or "natural walk cycle",
            )
        )
    elif primary == "sitting":
        a = min(1.2, dur * 0.35)
        cues.append(
            LocomotionCue(0.0, round(a, 3), "standing", 0.35, "forward", 0.1, character_id, "approach seat")
        )
        cues.append(
            LocomotionCue(
                round(a, 3),
                round(dur, 3),
                "sitting",
                0.5,
                "forward",
                0.05,
                character_id,
                "settle seated",
            )
        )
    elif primary == "turning":
        mid = dur * 0.45
        cues.append(
            LocomotionCue(0.0, round(mid, 3), "standing", 0.3, direction, 0.08, character_id, "plant")
        )
        cues.append(
            LocomotionCue(
                round(mid, 3),
                round(min(dur, mid + 1.2), 3),
                "turning",
                intensity,
                "left" if direction == "forward" else direction,
                _speed_for("turning", intensity),
                character_id,
                "pivot turn",
            )
        )
        if mid + 1.2 < dur:
            cues.append(
                LocomotionCue(
                    round(mid + 1.2, 3),
                    round(dur, 3),
                    "standing",
                    0.35,
                    direction,
                    0.05,
                    character_id,
                    "hold after turn",
                )
            )
    elif primary == "looking":
        cues.append(
            LocomotionCue(0.0, round(dur, 3), "standing", 0.3, direction, 0.05, character_id, "look hold")
        )
        cues.append(
            LocomotionCue(
                round(min(0.3, dur * 0.1), 3),
                round(min(dur, dur * 0.6), 3),
                "looking",
                intensity,
                direction,
                0.12,
                character_id,
                "gaze shift",
            )
        )
    else:
        # standing / idle — subtle presence
        cues.append(
            LocomotionCue(
                0.0,
                round(dur, 3),
                "standing",
                0.35,
                "forward",
                0.05,
                character_id,
                "natural stand with micro-shift",
            )
        )

    return cues


def actions_from_scene(scene: dict[str, Any]) -> list[str]:
    actions = scene.get("actions") or []
    if isinstance(actions, list):
        return [str(a) for a in actions if a]
    if isinstance(actions, str):
        return [actions]
    return []

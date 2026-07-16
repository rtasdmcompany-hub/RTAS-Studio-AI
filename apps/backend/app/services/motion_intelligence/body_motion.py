"""Body motion planning — weight, lean, breath, posture."""

from __future__ import annotations

from app.services.motion_intelligence.models import BodyMotionCue, LocomotionKind


def plan_body_motion(
    *,
    duration_seconds: float,
    text: str,
    primary: LocomotionKind,
    character_id: str | None,
    emotion: str | None = None,
) -> list[BodyMotionCue]:
    dur = max(1.0, float(duration_seconds or 4.0))
    t = (text or "").lower()
    emo = (emotion or "").lower()
    cues: list[BodyMotionCue] = []

    # Continuous subtle breath
    breath_end = round(dur, 3)
    breath_intensity = 0.25
    if emo in ("sad", "somber", "lonely"):
        breath_intensity = 0.35
    elif emo in ("excited", "angry", "intense"):
        breath_intensity = 0.4
    cues.append(
        BodyMotionCue(0.0, breath_end, "breath", breath_intensity, "center", character_id, "breath cycle")
    )

    if primary in ("walking", "running"):
        cues.append(
            BodyMotionCue(
                0.0,
                breath_end,
                "weight_shift",
                0.55 if primary == "walking" else 0.75,
                "center",
                character_id,
                "locomotion weight transfer",
            )
        )
        if primary == "running":
            cues.append(
                BodyMotionCue(0.2, breath_end, "lean", 0.45, "forward", character_id, "run lean")
            )
    elif primary == "sitting":
        cues.append(
            BodyMotionCue(0.0, min(1.0, dur * 0.3), "crouch", 0.5, "forward", character_id, "sit down")
        )
        cues.append(
            BodyMotionCue(
                min(1.0, dur * 0.3),
                breath_end,
                "posture",
                0.4,
                "center",
                character_id,
                "seated posture",
            )
        )
    elif primary == "turning":
        mid = dur * 0.4
        cues.append(
            BodyMotionCue(
                round(mid, 3),
                round(min(dur, mid + 1.0), 3),
                "twist",
                0.6,
                "left" if "left" in t else "right",
                character_id,
                "body turn lead",
            )
        )
    else:
        # Standing — weight shift + occasional lean
        cues.append(
            BodyMotionCue(
                round(dur * 0.25, 3),
                round(min(dur, dur * 0.25 + 1.2), 3),
                "weight_shift",
                0.35,
                "left",
                character_id,
                "natural weight transfer",
            )
        )
        if dur > 3.5:
            cues.append(
                BodyMotionCue(
                    round(dur * 0.55, 3),
                    round(min(dur, dur * 0.55 + 1.0), 3),
                    "shoulder_roll",
                    0.25,
                    "center",
                    character_id,
                    "idle shoulder ease",
                )
            )

    if any(w in t for w in ("lean", "leaning", "closer")):
        cues.append(
            BodyMotionCue(round(dur * 0.3, 3), breath_end, "lean", 0.5, "forward", character_id, "motivated lean")
        )

    return cues

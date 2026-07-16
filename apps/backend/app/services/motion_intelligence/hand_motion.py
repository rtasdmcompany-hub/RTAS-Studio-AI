"""Hand motion planning for natural human animation."""

from __future__ import annotations

from app.services.motion_intelligence.models import HandMotionCue, LocomotionKind


def plan_hand_motion(
    *,
    duration_seconds: float,
    text: str,
    primary: LocomotionKind,
    character_id: str | None,
    emotion: str | None = None,
) -> list[HandMotionCue]:
    dur = max(1.0, float(duration_seconds or 4.0))
    t = (text or "").lower()
    emo = (emotion or "").lower()
    cues: list[HandMotionCue] = []

    # Default: rest with occasional gesture
    cues.append(
        HandMotionCue(0.0, round(min(0.6, dur * 0.15), 3), "rest", "both", 0.2, character_id, "settle")
    )

    if any(w in t for w in ("point", "pointing", "indicate")):
        mid = dur * 0.35
        cues.append(
            HandMotionCue(
                round(mid, 3),
                round(min(dur, mid + 1.4), 3),
                "point",
                "right",
                0.7,
                character_id,
                "pointing beat",
            )
        )
    elif any(w in t for w in ("wave", "waving", "hello", "greet")):
        mid = dur * 0.25
        cues.append(
            HandMotionCue(
                round(mid, 3),
                round(min(dur, mid + 1.6), 3),
                "wave",
                "right",
                0.65,
                character_id,
                "greeting wave",
            )
        )
    elif any(w in t for w in ("hold", "holding", "carry", "phone", "cup", "bag")):
        cues.append(
            HandMotionCue(0.4, round(dur, 3), "hold", "right", 0.55, character_id, "object hold")
        )
    elif any(w in t for w in ("reach", "reaching", "grab", "take")):
        mid = dur * 0.4
        cues.append(
            HandMotionCue(
                round(mid, 3),
                round(min(dur, mid + 1.2), 3),
                "reach",
                "right",
                0.6,
                character_id,
                "reach",
            )
        )
    elif primary in ("walking", "running"):
        # Arm swing as secondary motion
        cues.append(
            HandMotionCue(
                0.3,
                round(dur, 3),
                "gesture",
                "both",
                0.4 if primary == "walking" else 0.65,
                character_id,
                "arm swing with locomotion",
            )
        )
    elif any(w in t for w in ("talk", "speak", "explain", "present", "dialogue")) or emo in (
        "confident",
        "excited",
        "happy",
    ):
        step = 1.8
        t0 = 0.5
        i = 0
        while t0 < dur:
            end = min(dur, t0 + 0.9)
            cues.append(
                HandMotionCue(
                    round(t0, 3),
                    round(end, 3),
                    "emphasize" if i % 2 == 0 else "gesture",
                    "right" if i % 2 == 0 else "left",
                    0.45,
                    character_id,
                    "speech gesture",
                )
            )
            t0 += step
            i += 1
    else:
        # Idle micro hand rest
        if dur > 2.0:
            cues.append(
                HandMotionCue(
                    round(dur * 0.4, 3),
                    round(min(dur, dur * 0.4 + 0.8), 3),
                    "gesture",
                    "left",
                    0.25,
                    character_id,
                    "idle hand shift",
                )
            )

    return cues

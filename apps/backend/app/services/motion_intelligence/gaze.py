"""Looking / gaze planning for Motion Intelligence."""

from __future__ import annotations

from app.services.motion_intelligence.models import GazeCue, LocomotionKind


def plan_gaze_cues(
    *,
    duration_seconds: float,
    text: str,
    primary: LocomotionKind,
    character_id: str | None,
    camera_framing: str | None = None,
) -> list[GazeCue]:
    dur = max(1.0, float(duration_seconds or 4.0))
    t = (text or "").lower()
    framing = (camera_framing or "").lower()

    target = "camera"
    if any(w in t for w in ("look away", "offscreen", "off screen", "horizon")):
        target = "offscreen"
    elif any(w in t for w in ("look at", "toward", "watch", "stare at")):
        if "camera" in t:
            target = "camera"
        elif any(w in t for w in ("him", "her", "them", "person", "character")):
            target = "character"
        else:
            target = "object"
    elif "environment" in t or "around" in t:
        target = "environment"
    elif "close" in framing or "close-up" in framing or "portrait" in framing:
        target = "camera"

    cues: list[GazeCue] = []

    # Establish look
    hold_end = min(dur, max(1.2, dur * 0.45))
    cues.append(
        GazeCue(
            start_sec=0.0,
            end_sec=round(hold_end, 3),
            target=target,
            yaw=0.0,
            pitch=-0.05 if target == "camera" else 0.0,
            hold=True,
            character_id=character_id,
        )
    )

    # Natural glance / reacquire
    if dur > 2.5:
        glance_start = hold_end
        glance_end = min(dur, glance_start + 0.7)
        yaw = 0.18 if primary in ("turning", "looking", "walking") else 0.1
        if "left" in t:
            yaw = -abs(yaw)
        cues.append(
            GazeCue(
                start_sec=round(glance_start, 3),
                end_sec=round(glance_end, 3),
                target="environment" if target == "camera" else target,
                yaw=round(yaw, 3),
                pitch=0.04,
                hold=False,
                character_id=character_id,
            )
        )
        if glance_end < dur:
            cues.append(
                GazeCue(
                    start_sec=round(glance_end, 3),
                    end_sec=round(dur, 3),
                    target=target,
                    yaw=0.0,
                    pitch=-0.03,
                    hold=True,
                    character_id=character_id,
                )
            )

    return cues

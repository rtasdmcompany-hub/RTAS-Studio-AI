"""Emotion Timeline Engine."""

from __future__ import annotations

import hashlib

from app.services.emotion_intelligence.models import EmotionTimelineEvent


def build_emotion_timeline(
    *,
    job_id: str,
    primary: str,
    secondary: str | None,
    duration_sec: float,
    intensity: float,
) -> list[EmotionTimelineEvent]:
    dur = max(1.0, float(duration_sec))
    events: list[EmotionTimelineEvent] = []
    if secondary and secondary != primary:
        mid = dur * 0.55
        events.append(
            EmotionTimelineEvent(
                event_id=_eid(job_id, 0),
                start_sec=0.0,
                end_sec=round(mid, 3),
                emotion=primary,
                intensity=round(intensity, 3),
                expression_id=f"expr_{primary}",
            )
        )
        events.append(
            EmotionTimelineEvent(
                event_id=_eid(job_id, 1),
                start_sec=round(mid, 3),
                end_sec=round(dur, 3),
                emotion=secondary,
                intensity=round(max(0.2, intensity * 0.9), 3),
                expression_id=f"expr_{secondary}",
            )
        )
    else:
        events.append(
            EmotionTimelineEvent(
                event_id=_eid(job_id, 0),
                start_sec=0.0,
                end_sec=round(dur, 3),
                emotion=primary,
                intensity=round(intensity, 3),
                expression_id=f"expr_{primary}",
            )
        )
    return events


def _eid(job_id: str, idx: int) -> str:
    digest = hashlib.sha1(f"{job_id}|{idx}".encode()).hexdigest()
    return f"eevt_{digest[:10]}"

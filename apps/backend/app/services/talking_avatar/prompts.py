"""Talking avatar provider prompt assembly."""

from __future__ import annotations

from typing import Any

from app.services.talking_avatar.face_lock import face_lock_prompt
from app.services.talking_avatar.models import FaceLock


def build_avatar_prompt(
    *,
    prompt: str,
    face_lock: FaceLock,
    emotion: str,
    director_notes: list[str] | None,
    character: dict[str, Any] | None,
    natural_motion: bool,
) -> str:
    parts = [
        (prompt or "Professional talking avatar presenter").strip(),
        "Talking avatar / digital human close-up, shoulders-up framing.",
        f"Emotion={emotion}.",
        "Face animation with accurate lip sync, natural head motion, eye contact,",
        "subtle blinks, micro-expressions, and idle breathing motion.",
    ]
    if natural_motion:
        parts.append("Natural organic motion — avoid robotic stiffness.")
    else:
        parts.append("Controlled presenter motion — stable and clear.")
    parts.append(face_lock_prompt(face_lock, character))
    if director_notes:
        parts.append("Director: " + "; ".join(director_notes[:3]) + ".")
    parts.append(
        "Photoreal talking head, consistent identity, no morphing, "
        "no watermark, no burned-in captions."
    )
    return " ".join(p for p in parts if p).strip()[:2000]

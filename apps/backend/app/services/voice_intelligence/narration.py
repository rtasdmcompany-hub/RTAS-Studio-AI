"""Narration Manager — narrator / VO / thought track summaries."""

from __future__ import annotations

from typing import Any

from app.services.voice_intelligence.models import DialogueLine


def build_narration_summary(lines: list[DialogueLine]) -> dict[str, Any]:
    narrator = [ln for ln in lines if ln.is_narration]
    voice_over = [ln for ln in lines if ln.is_voice_over]
    thoughts = [ln for ln in lines if ln.is_internal]
    group = [ln for ln in lines if ln.is_group]
    character_lines = [
        ln
        for ln in lines
        if ln.role in ("character_a", "character_b", "character_c")
    ]

    def _pack(items: list[DialogueLine]) -> dict[str, Any]:
        return {
            "count": len(items),
            "total_speaking_sec": round(sum(i.speaking_duration_sec for i in items), 3),
            "line_ids": [i.line_id for i in items],
            "texts": [i.text for i in items[:20]],
        }

    return {
        "narrator": _pack(narrator),
        "voice_over": _pack(voice_over),
        "internal_thoughts": _pack(thoughts),
        "group_dialogue": _pack(group),
        "character_dialogue": _pack(character_lines),
        "narration_generated": len(narrator) + len(voice_over) > 0,
        "recommended_mix": {
            "dialogue_priority": True,
            "narration_duck_db": -6.0 if character_lines and (narrator or voice_over) else 0.0,
            "thought_reverb": True if thoughts else False,
        },
    }

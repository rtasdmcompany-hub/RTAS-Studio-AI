"""Dialogue Planner — detect narrator, characters, group, thoughts, VO."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from app.services.voice_intelligence.emotions import detect_emotion
from app.services.voice_intelligence.models import DialogueLine, DialogueRole

_ROLE_PATTERNS: list[tuple[re.Pattern[str], DialogueRole, str | None]] = [
    (re.compile(r"^\s*(narrator|narration)\s*[:\-—]\s*", re.I), "narrator", None),
    (re.compile(r"^\s*(voice[\s\-]?over|vo)\s*[:\-—]\s*", re.I), "voice_over", None),
    (re.compile(r"^\s*(internal|thought|inner)\s*[:\-—]\s*", re.I), "internal_thought", None),
    (re.compile(r"^\s*(group|crowd|all)\s*[:\-—]\s*", re.I), "group", None),
    (re.compile(r"^\s*(character[_\s\-]?a|char\s*a|a)\s*[:\-—]\s*", re.I), "character_a", "Character_A"),
    (re.compile(r"^\s*(character[_\s\-]?b|char\s*b|b)\s*[:\-—]\s*", re.I), "character_b", "Character_B"),
    (re.compile(r"^\s*(character[_\s\-]?c|char\s*c|c)\s*[:\-—]\s*", re.I), "character_c", "Character_C"),
]


def _split_script(script: str) -> list[str]:
    raw = (script or "").replace("\r\n", "\n").strip()
    if not raw:
        return []
    parts = [p.strip() for p in re.split(r"\n+", raw) if p.strip()]
    if len(parts) == 1:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", parts[0]) if s.strip()]
        return sentences if sentences else parts
    return parts


def _detect_role(raw_line: str) -> tuple[DialogueRole, str, str | None]:
    for pattern, role, slot in _ROLE_PATTERNS:
        m = pattern.match(raw_line)
        if m:
            return role, raw_line[m.end() :].strip() or raw_line, slot
    lower = raw_line.lower()
    if lower.startswith("(") and "think" in lower:
        return "internal_thought", raw_line.strip("() "), None
    if lower.startswith("[vo]") or lower.startswith("[voice-over]"):
        text = re.sub(r"^\[(vo|voice-over)\]\s*", "", raw_line, flags=re.I).strip()
        return "voice_over", text, None
    if lower.startswith("[narrator]") or lower.startswith("[narration]"):
        text = re.sub(r"^\[(narrator|narration)\]\s*", "", raw_line, flags=re.I).strip()
        return "narrator", text, None
    return "narrator", raw_line, None


def _line_id(project_id: str, index: int, text: str) -> str:
    digest = hashlib.sha1(f"{project_id}|{index}|{text}".encode()).hexdigest()
    return f"dlg_{digest[:12]}"


def plan_dialogue(
    script: str,
    *,
    project_id: str = "proj",
    default_emotion: str = "calm",
) -> list[DialogueLine]:
    parts = _split_script(script)
    lines: list[DialogueLine] = []
    char_cycle = ["character_a", "character_b", "character_c"]
    char_idx = 0
    unlabeled_count = 0

    for i, raw in enumerate(parts):
        role, text, slot = _detect_role(raw)
        labeled = any(p.match(raw) for p, _, _ in _ROLE_PATTERNS) or raw.strip().startswith(
            ("[", "(")
        )
        if not labeled and role == "narrator" and unlabeled_count > 0:
            role = char_cycle[char_idx % 3]  # type: ignore[assignment]
            slot = f"Character_{chr(65 + (char_idx % 3))}"
            char_idx += 1
        if not labeled and role == "narrator":
            unlabeled_count += 1
        elif labeled:
            unlabeled_count = 0

        emotion = detect_emotion(text, default=default_emotion)  # type: ignore[arg-type]
        lines.append(
            DialogueLine(
                line_id=_line_id(project_id, i, text),
                index=i,
                text=text,
                role=role,
                emotion=emotion,
                character_slot=slot,
                is_narration=role == "narrator",
                is_internal=role == "internal_thought",
                is_voice_over=role == "voice_over",
                is_group=role == "group",
            )
        )
    return lines


def dialogue_role_summary(lines: list[DialogueLine]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for ln in lines:
        counts[ln.role] = counts.get(ln.role, 0) + 1
    return {
        "roles_detected": sorted(counts.keys()),
        "counts": counts,
        "has_narrator": counts.get("narrator", 0) > 0,
        "has_characters": any(
            counts.get(r, 0) > 0 for r in ("character_a", "character_b", "character_c")
        ),
        "has_group": counts.get("group", 0) > 0,
        "has_internal": counts.get("internal_thought", 0) > 0,
        "has_voice_over": counts.get("voice_over", 0) > 0,
        "line_count": len(lines),
    }

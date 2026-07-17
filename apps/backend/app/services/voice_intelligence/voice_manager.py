"""Voice Manager — permanent character voice profiles + assignment."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.voice_intelligence.emotions import emotion_delivery_hints
from app.services.voice_intelligence.models import (
    AgeGroup,
    CharacterVoiceProfile,
    DialogueLine,
    EmotionTone,
)

_ROLE_DEFAULTS: dict[str, dict[str, Any]] = {
    "narrator": {
        "gender": "neutral",
        "age_group": "adult",
        "accent": "neutral",
        "speaking_speed": 0.95,
        "pitch": 1.0,
        "energy": 0.55,
        "emotion_style": "calm",
        "narration_style": "documentary",
        "voice_suffix": "narrator",
    },
    "voice_over": {
        "gender": "neutral",
        "age_group": "adult",
        "accent": "neutral",
        "speaking_speed": 0.92,
        "pitch": 0.98,
        "energy": 0.5,
        "emotion_style": "serious",
        "narration_style": "commercial_vo",
        "voice_suffix": "vo",
    },
    "internal_thought": {
        "gender": "neutral",
        "age_group": "adult",
        "accent": "neutral",
        "speaking_speed": 0.88,
        "pitch": 0.94,
        "energy": 0.4,
        "emotion_style": "emotional",
        "narration_style": "intimate_thought",
        "voice_suffix": "inner",
    },
    "group": {
        "gender": "neutral",
        "age_group": "adult",
        "accent": "neutral",
        "speaking_speed": 1.05,
        "pitch": 1.02,
        "energy": 0.75,
        "emotion_style": "excited",
        "narration_style": "crowd",
        "voice_suffix": "group",
    },
    "character_a": {
        "gender": "female",
        "age_group": "young_adult",
        "accent": "neutral",
        "speaking_speed": 1.0,
        "pitch": 1.05,
        "energy": 0.65,
        "emotion_style": "calm",
        "narration_style": "conversational",
        "voice_suffix": "char_a",
        "slot": "Character_A",
    },
    "character_b": {
        "gender": "male",
        "age_group": "adult",
        "accent": "neutral",
        "speaking_speed": 1.0,
        "pitch": 0.95,
        "energy": 0.6,
        "emotion_style": "serious",
        "narration_style": "conversational",
        "voice_suffix": "char_b",
        "slot": "Character_B",
    },
    "character_c": {
        "gender": "female",
        "age_group": "adult",
        "accent": "soft",
        "speaking_speed": 0.98,
        "pitch": 1.02,
        "energy": 0.58,
        "emotion_style": "emotional",
        "narration_style": "conversational",
        "voice_suffix": "char_c",
        "slot": "Character_C",
    },
}


def _voice_id(language: str, role: str, gender: str) -> str:
    lang = (language or "en").split("-")[0].lower()
    digest = hashlib.sha1(f"{lang}|{role}|{gender}".encode()).hexdigest()[:8]
    return f"rtas_{lang}_{gender}_{digest}"


def build_profile_for_role(
    role: str,
    *,
    language: str = "en",
    overrides: dict[str, Any] | None = None,
) -> CharacterVoiceProfile:
    base = dict(_ROLE_DEFAULTS.get(role, _ROLE_DEFAULTS["narrator"]))
    if overrides:
        base.update({k: v for k, v in overrides.items() if v is not None})
    gender = str(base.get("gender") or "neutral")
    age_group = str(base.get("age_group") or "adult")
    if age_group not in ("child", "teen", "young_adult", "adult", "senior"):
        age_group = "adult"
    emotion_style = str(base.get("emotion_style") or "calm")
    voice_id = str(base.get("voice_id") or _voice_id(language, role, gender))
    return CharacterVoiceProfile(
        voice_id=voice_id,
        gender=gender,
        age_group=age_group,  # type: ignore[arg-type]
        language=(language or "en").split("-")[0].lower(),
        accent=str(base.get("accent") or "neutral"),
        speaking_speed=float(base.get("speaking_speed") or 1.0),
        pitch=float(base.get("pitch") or 1.0),
        energy=float(base.get("energy") or 0.5),
        emotion_style=emotion_style,  # type: ignore[arg-type]
        narration_style=str(base.get("narration_style") or "conversational"),
        character_slot=base.get("slot"),
        character_id=base.get("character_id"),
    )


def assign_voices(
    lines: list[DialogueLine],
    *,
    language: str = "en",
    profile_overrides: dict[str, dict[str, Any]] | None = None,
) -> dict[str, CharacterVoiceProfile]:
    overrides = profile_overrides or {}
    roles = {ln.role for ln in lines}
    # Always ensure narrator profile available for narration manager
    roles.add("narrator")
    profiles: dict[str, CharacterVoiceProfile] = {}
    for role in sorted(roles):
        profiles[role] = build_profile_for_role(
            role, language=language, overrides=overrides.get(role)
        )

    for line in lines:
        profile = profiles[line.role]
        hints = emotion_delivery_hints(line.emotion)
        # Line keeps permanent voice_id; emotion only modulates delivery metadata
        line.voice_id = profile.voice_id
        if not line.character_slot and profile.character_slot:
            line.character_slot = profile.character_slot
        # Soft-update energy display via profile remains permanent; line emotion stays
        _ = hints  # used by timing/consistency consumers
    return profiles


def apply_manual_assignments(
    profiles: dict[str, CharacterVoiceProfile],
    assignments: list[dict[str, Any]] | None,
    *,
    language: str = "en",
) -> dict[str, CharacterVoiceProfile]:
    if not assignments:
        return profiles
    updated = dict(profiles)
    for item in assignments:
        role = str(item.get("role") or item.get("character_slot") or "").strip().lower()
        role = role.replace("character_a", "character_a").replace("-", "_")
        slot_map = {
            "character_a": "character_a",
            "a": "character_a",
            "character_b": "character_b",
            "b": "character_b",
            "character_c": "character_c",
            "c": "character_c",
            "narrator": "narrator",
            "voice_over": "voice_over",
            "vo": "voice_over",
            "internal_thought": "internal_thought",
            "group": "group",
        }
        resolved = slot_map.get(role, role)
        if not resolved:
            continue
        existing = updated.get(resolved)
        overrides = {
            "voice_id": item.get("voice_id") or item.get("voiceId"),
            "gender": item.get("gender"),
            "age_group": item.get("age_group") or item.get("ageGroup"),
            "accent": item.get("accent"),
            "speaking_speed": item.get("speaking_speed") or item.get("speakingSpeed"),
            "pitch": item.get("pitch"),
            "energy": item.get("energy"),
            "emotion_style": item.get("emotion_style") or item.get("emotionStyle"),
            "narration_style": item.get("narration_style") or item.get("narrationStyle"),
            "character_id": item.get("character_id") or item.get("characterId"),
            "slot": existing.character_slot if existing else item.get("character_slot"),
        }
        if existing:
            overrides = {**existing.to_dict(), **{k: v for k, v in overrides.items() if v is not None}}
        updated[resolved] = build_profile_for_role(
            resolved, language=language, overrides=overrides
        )
    return updated

"""Character Memory ↔ Character Voice Profile bridge."""

from __future__ import annotations

from typing import Any

from app.services.voice_cloning import store
from app.services.voice_cloning.cache import cache_get, cache_set
from app.services.voice_cloning.models import CharacterVoiceProfile


def age_to_group(age: str | None) -> str:
    a = (age or "adult").lower().strip()
    if a in ("child", "kid"):
        return "child"
    if a in ("teen", "teenager"):
        return "teen"
    if a in ("elder", "elderly", "senior"):
        return "elder"
    return "adult"


def default_voice_for(gender: str, language: str = "en") -> str:
    g = (gender or "female").lower()
    if g not in ("male", "female"):
        g = "female"
    lang = (language or "en").lower().split("-")[0]
    return f"rtas_{lang}_{g}_01"


def profile_from_character_memory(mem: dict[str, Any] | Any) -> CharacterVoiceProfile:
    """Build / restore CharacterVoiceProfile from Character Memory dict or object."""
    if hasattr(mem, "to_dict"):
        data = mem.to_dict()
    else:
        data = dict(mem or {})

    character_id = str(data.get("character_id") or "Character_A")
    cached = cache_get(f"char_voice:{character_id}")
    existing = store.get_character(character_id)
    if existing:
        cache_set(f"char_voice:{character_id}", existing.to_dict())
        return existing
    if cached and isinstance(cached, dict):
        return CharacterVoiceProfile(
            character_id=character_id,
            clone_id=cached.get("clone_id"),
            default_voice=str(cached.get("default_voice") or default_voice_for(
                str(data.get("gender") or "female"),
                str(cached.get("language") or data.get("language") or "en"),
            )),
            language=str(cached.get("language") or data.get("language") or "en"),
            accent=str(cached.get("accent") or data.get("accent") or "neutral"),
            speaking_style=str(
                cached.get("speaking_style") or data.get("speaking_style") or "natural"
            ),
            emotion_profile=str(
                cached.get("emotion_profile") or data.get("emotion_profile") or "calm"
            ),
            gender=str(data.get("gender") or cached.get("gender") or "unspecified"),
            age_group=str(
                cached.get("age_group")
                or data.get("age_group")
                or age_to_group(str(data.get("age") or "adult"))
            ),
            voice_version=int(cached.get("voice_version") or 1),
            voice_metadata=dict(cached.get("voice_metadata") or data.get("voice_metadata") or {}),
            voice_locked=bool(cached.get("voice_locked") or data.get("voice_locked")),
            speaker_id=cached.get("speaker_id") or data.get("speaker_id"),
            preview_url=cached.get("preview_url") or data.get("preview_url"),
        )

    language = str(data.get("language") or "en")
    gender = str(data.get("gender") or "unspecified")
    profile = CharacterVoiceProfile(
        character_id=character_id,
        clone_id=data.get("clone_id") or data.get("voice_clone_id"),
        default_voice=str(
            data.get("default_voice")
            or data.get("voice_id")
            or default_voice_for(gender, language)
        ),
        language=language,
        accent=str(data.get("accent") or "neutral"),
        speaking_style=str(data.get("speaking_style") or "natural"),
        emotion_profile=str(data.get("emotion_profile") or "calm"),
        gender=gender,
        age_group=str(data.get("age_group") or age_to_group(str(data.get("age") or "adult"))),
        voice_version=int(data.get("voice_version") or 1),
        voice_metadata=dict(data.get("voice_metadata") or {}),
        voice_locked=bool(data.get("voice_locked") or False),
        speaker_id=data.get("speaker_id"),
        preview_url=data.get("preview_url") or data.get("voice_preview_url"),
    )
    store.put_character(profile)
    cache_set(f"char_voice:{character_id}", profile.to_dict())
    return profile


def assign_clone_to_character(
    character_id: str,
    clone_id: str,
    *,
    lock: bool = True,
    language: str | None = None,
    accent: str | None = None,
    speaking_style: str | None = None,
    emotion_profile: str | None = None,
    gender: str | None = None,
    age_group: str | None = None,
    default_voice: str | None = None,
    preview_url: str | None = None,
    speaker_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> CharacterVoiceProfile:
    existing = store.get_character(character_id)
    if existing and existing.voice_locked and existing.clone_id and existing.clone_id != clone_id:
        raise PermissionError(
            f"Character '{character_id}' voice is locked to clone '{existing.clone_id}'"
        )

    base = existing or CharacterVoiceProfile(
        character_id=character_id,
        clone_id=None,
        default_voice=default_voice or default_voice_for(gender or "female", language or "en"),
        language=language or "en",
        accent=accent or "neutral",
        speaking_style=speaking_style or "natural",
        emotion_profile=emotion_profile or "calm",
        gender=gender or "unspecified",
        age_group=age_group or "adult",
        voice_version=1,
    )

    clone = store.get_clone(clone_id)
    profile = CharacterVoiceProfile(
        character_id=character_id,
        clone_id=clone_id,
        default_voice=default_voice
        or (f"clone:{clone_id}" if clone else base.default_voice),
        language=language or (clone.language if clone else base.language),
        accent=accent or (clone.accent if clone else base.accent),
        speaking_style=speaking_style
        or (clone.speaking_style if clone else base.speaking_style),
        emotion_profile=emotion_profile
        or (clone.emotion_profile if clone else base.emotion_profile),
        gender=gender or (clone.gender if clone else base.gender),
        age_group=age_group or (clone.age_group if clone else base.age_group),
        voice_version=(clone.voice_version if clone else base.voice_version),
        voice_metadata={
            **base.voice_metadata,
            **(metadata or {}),
            "assigned_clone_id": clone_id,
        },
        voice_locked=lock if lock is not None else base.voice_locked,
        speaker_id=speaker_id
        or (clone.speaker.speaker_id if clone and clone.speaker else base.speaker_id),
        preview_url=preview_url
        or (clone.preview_url if clone else base.preview_url),
    )
    store.put_character(profile)
    cache_set(f"char_voice:{character_id}", profile.to_dict())
    return profile


def restore_voice_for_generation(
    character_memory: list[dict[str, Any]] | None,
) -> CharacterVoiceProfile | None:
    """Automatically restore the correct voice during every generation."""
    if not character_memory:
        return None
    lead = character_memory[0]
    return profile_from_character_memory(lead)


def enrich_character_memory_dicts(
    memories: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Ensure each character memory dict permanently carries voice fields."""
    out: list[dict[str, Any]] = []
    for mem in memories:
        profile = profile_from_character_memory(mem)
        merged = dict(mem)
        merged.update(
            {
                "default_voice": profile.default_voice,
                "voice_id": profile.default_voice,
                "language": profile.language,
                "accent": profile.accent,
                "speaking_style": profile.speaking_style,
                "emotion_profile": profile.emotion_profile,
                "age_group": profile.age_group,
                "voice_version": profile.voice_version,
                "voice_metadata": profile.voice_metadata,
                "voice_locked": profile.voice_locked,
                "clone_id": profile.clone_id,
                "speaker_id": profile.speaker_id,
                "preview_url": profile.preview_url,
            }
        )
        out.append(merged)
    return out

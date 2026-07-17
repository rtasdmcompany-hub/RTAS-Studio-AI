"""Voice presets and catalog — male/female, multi-language, replaceable providers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from app.services.voice_generation.languages import list_languages, normalize_language

Gender = Literal["male", "female", "neutral"]


@dataclass(frozen=True)
class VoicePreset:
    voice_id: str
    name: str
    language: str
    gender: Gender
    style: str = "natural"
    provider_model: str = "simulation-tts-v1"
    sample_rate: int = 24000
    description: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["tags"] = list(self.tags)
        return d


def _build_default_catalog() -> list[VoicePreset]:
    catalog: list[VoicePreset] = []
    styles = {
        "en": ("Narrator", "Studio Host", "Warm Companion"),
        "ur": ("Urdu Narrator", "Studio Host UR", "Warm UR"),
        "hi": ("Hindi Narrator", "Studio Host HI", "Warm HI"),
        "ar": ("Arabic Narrator", "Studio Host AR", "Warm AR"),
        "pa": ("Punjabi Narrator", "Studio Host PA", "Warm PA"),
    }
    for lang in ("en", "ur", "hi", "ar", "pa"):
        names = styles[lang]
        catalog.append(
            VoicePreset(
                voice_id=f"rtas_{lang}_male_01",
                name=f"{names[0]} (Male)",
                language=lang,
                gender="male",
                style="narrative",
                tags=("preset", "male", lang),
                description=f"Natural male voice for {lang}",
            )
        )
        catalog.append(
            VoicePreset(
                voice_id=f"rtas_{lang}_female_01",
                name=f"{names[1]} (Female)",
                language=lang,
                gender="female",
                style="broadcast",
                tags=("preset", "female", lang),
                description=f"Natural female voice for {lang}",
            )
        )
        catalog.append(
            VoicePreset(
                voice_id=f"rtas_{lang}_female_02",
                name=f"{names[2]} (Female Soft)",
                language=lang,
                gender="female",
                style="soft",
                tags=("preset", "female", "soft", lang),
                description=f"Soft female voice for {lang}",
            )
        )
    return catalog


_CATALOG: dict[str, VoicePreset] = {v.voice_id: v for v in _build_default_catalog()}


def list_voices(
    *,
    language: str | None = None,
    gender: str | None = None,
) -> list[dict[str, Any]]:
    lang = normalize_language(language) if language else None
    g = gender.strip().lower() if gender else None
    out = []
    for voice in sorted(_CATALOG.values(), key=lambda v: (v.language, v.gender, v.voice_id)):
        if lang and voice.language != lang:
            continue
        if g and voice.gender != g:
            continue
        out.append(voice.to_dict())
    return out


def get_voice(voice_id: str) -> VoicePreset:
    key = (voice_id or "").strip()
    if key not in _CATALOG:
        raise ValueError(f"Unknown voice_id '{voice_id}'")
    return _CATALOG[key]


def voices_payload() -> dict[str, Any]:
    return {
        "languages": list_languages(),
        "voices": list_voices(),
        "count": len(_CATALOG),
    }

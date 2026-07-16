"""Phoneme → viseme mapping (professional mouth shapes)."""

from __future__ import annotations

from app.services.lip_sync.models import PhonemeToken, SupportedLanguage, VisemeCue

# Standard viseme set used across languages
_PHONEME_TO_VISEME: dict[str, tuple[str, float, float, float]] = {
    # viseme, openness, lip_round, lip_width
    "AA": ("AA", 0.78, 0.15, 0.55),
    "P": ("PP", 0.28, 0.1, 0.4),
    "M": ("PP", 0.22, 0.1, 0.35),
    "F": ("FF", 0.42, 0.05, 0.5),
    "S": ("SS", 0.32, 0.05, 0.55),
    "SH": ("SS", 0.35, 0.25, 0.45),
    "CH": ("SS", 0.38, 0.2, 0.45),
    "T": ("DD", 0.36, 0.05, 0.5),
    "D": ("DD", 0.38, 0.05, 0.5),
    "N": ("DD", 0.3, 0.05, 0.45),
    "K": ("KK", 0.4, 0.1, 0.45),
    "H": ("AA", 0.5, 0.1, 0.5),
    "L": ("L", 0.4, 0.1, 0.5),
    "R": ("RR", 0.42, 0.2, 0.45),
    "W": ("OU", 0.55, 0.75, 0.3),
    "Y": ("I", 0.45, 0.15, 0.6),
    "SIL": ("REST", 0.08, 0.05, 0.35),
    "REST": ("REST", 0.1, 0.05, 0.35),
}

# Language-specific openness bias (speech style)
_LANG_OPENNESS_BIAS: dict[SupportedLanguage, float] = {
    "en": 0.0,
    "ur": 0.04,
    "ar": 0.06,
    "hi": 0.03,
    "pa": 0.05,
}


def map_phoneme_to_viseme(
    phoneme: str,
    language: SupportedLanguage,
) -> tuple[str, float, float, float]:
    base = _PHONEME_TO_VISEME.get(phoneme.upper(), ("REST", 0.15, 0.05, 0.35))
    viseme, openness, roundness, width = base
    openness = min(1.0, max(0.0, openness + _LANG_OPENNESS_BIAS.get(language, 0.0)))
    return viseme, openness, roundness, width


def phonemes_to_visemes(
    phonemes: list[PhonemeToken],
    *,
    emotion: str,
    emotion_intensity: float,
    dialogue: str,
    openness_scale: float = 1.0,
) -> list[VisemeCue]:
    cues: list[VisemeCue] = []
    snippet = (dialogue or "")[:100]
    for p in phonemes:
        viseme, openness, roundness, width = map_phoneme_to_viseme(p.phoneme, p.language)
        openness = min(1.0, openness * openness_scale * (0.85 + 0.3 * p.stress))
        jaw = min(1.0, openness * 0.85)
        cues.append(
            VisemeCue(
                index=p.index,
                start_sec=p.start_sec,
                end_sec=p.end_sec,
                phoneme=p.phoneme,
                viseme=viseme,
                mouth_openness=round(openness, 3),
                jaw_drop=round(jaw, 3),
                lip_round=round(roundness, 3),
                lip_width=round(width, 3),
                emotion=emotion,
                emotion_intensity=emotion_intensity,
                language=p.language,
                dialogue_snippet=snippet,
                sync_confidence=0.88 if p.phoneme != "SIL" else 0.95,
            )
        )
    return cues

"""Models for Professional Lip Sync Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

SupportedLanguage = Literal["en", "ur", "ar", "hi", "pa"]


@dataclass
class PhonemeToken:
    index: int
    grapheme: str
    phoneme: str
    language: SupportedLanguage
    start_sec: float
    end_sec: float
    stress: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VisemeCue:
    index: int
    start_sec: float
    end_sec: float
    phoneme: str
    viseme: str
    mouth_openness: float
    jaw_drop: float
    lip_round: float
    lip_width: float
    emotion: str
    emotion_intensity: float
    language: SupportedLanguage
    dialogue_snippet: str = ""
    sync_confidence: float = 0.85

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SpeechAlignment:
    language: SupportedLanguage
    speech_start_sec: float
    speech_end_sec: float
    duration_seconds: float
    words: list[dict[str, Any]] = field(default_factory=list)
    pause_windows: list[dict[str, Any]] = field(default_factory=list)
    words_per_second: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LipSyncPlan:
    job_id: str
    language: SupportedLanguage
    languages_detected: list[str]
    emotion: str
    alignment: SpeechAlignment
    phonemes: list[PhonemeToken]
    visemes: list[VisemeCue]
    timeline: list[dict[str, Any]]
    dialogue: str
    character_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "language": self.language,
            "languages_detected": self.languages_detected,
            "emotion": self.emotion,
            "alignment": self.alignment.to_dict(),
            "phonemes": [p.to_dict() for p in self.phonemes],
            "visemes": [v.to_dict() for v in self.visemes],
            "timeline": self.timeline,
            "dialogue": self.dialogue,
            "character_id": self.character_id,
            "metadata": self.metadata,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "language": self.language,
            "emotion": self.emotion,
            "phonemes": len(self.phonemes),
            "visemes": len(self.visemes),
            "duration_seconds": self.alignment.duration_seconds,
            "languages_detected": self.languages_detected,
            "avg_confidence": round(
                (
                    sum(v.sync_confidence for v in self.visemes) / len(self.visemes)
                    if self.visemes
                    else 0.0
                ),
                3,
            ),
        }

    def to_audio_director_cues(self) -> list[dict[str, Any]]:
        """Bridge shape compatible with Audio Director LipSyncCue dicts."""
        out = []
        for v in self.visemes:
            out.append(
                {
                    "start_sec": v.start_sec,
                    "end_sec": v.end_sec,
                    "character_id": self.character_id or "lead",
                    "phoneme_hint": v.phoneme,
                    "mouth_openness": v.mouth_openness,
                    "viseme": v.viseme,
                    "dialogue_snippet": v.dialogue_snippet,
                    "sync_confidence": v.sync_confidence,
                    "language": v.language,
                    "emotion": v.emotion,
                }
            )
        return out

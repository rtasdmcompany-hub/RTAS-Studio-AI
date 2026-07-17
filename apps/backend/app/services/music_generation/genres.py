"""Pluggable genre registry — unlimited future genres without core changes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class GenreDef:
    code: str
    name: str
    default_bpm: int
    default_mood: str
    default_energy: float
    default_key: str
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["tags"] = list(self.tags)
        return d


_GENRES: dict[str, GenreDef] = {}


def _register_defaults() -> None:
    defaults = [
        GenreDef("cinematic", "Cinematic", 90, "dramatic", 0.6, "Cm", ("film", "score")),
        GenreDef("epic", "Epic", 120, "heroic", 0.9, "Dm", ("trailer", "orchestra")),
        GenreDef("emotional", "Emotional", 72, "tender", 0.4, "Am", ("strings",)),
        GenreDef("sad", "Sad", 68, "melancholy", 0.3, "Em", ("piano",)),
        GenreDef("romantic", "Romantic", 80, "warm", 0.45, "F", ("ballad",)),
        GenreDef("corporate", "Corporate", 110, "uplifting", 0.55, "C", ("business",)),
        GenreDef("documentary", "Documentary", 95, "reflective", 0.4, "G", ("narration",)),
        GenreDef("action", "Action", 140, "intense", 0.95, "E", ("drums",)),
        GenreDef("horror", "Horror", 70, "tense", 0.7, "F#m", ("dissonant",)),
        GenreDef("sci-fi", "Sci-Fi", 100, "futuristic", 0.65, "Bm", ("synth",)),
        GenreDef("hip-hop", "Hip-Hop", 90, "groovy", 0.7, "Gm", ("beats",)),
        GenreDef("lo-fi", "Lo-Fi", 85, "chill", 0.35, "C", ("study",)),
        GenreDef("orchestral", "Orchestral", 88, "grand", 0.75, "D", ("classical",)),
        GenreDef("electronic", "Electronic", 128, "energetic", 0.8, "Am", ("edm",)),
        GenreDef("ambient", "Ambient", 60, "calm", 0.25, "C", ("atmosphere",)),
        GenreDef("acoustic", "Acoustic", 96, "intimate", 0.4, "G", ("guitar",)),
    ]
    for g in defaults:
        _GENRES[g.code] = g


_register_defaults()


def register_genre(genre: GenreDef) -> None:
    """Add or replace a genre without modifying the core engine."""
    _GENRES[genre.code.lower().strip()] = genre


def normalize_genre(code: str | None) -> str:
    key = (code or "cinematic").lower().strip().replace(" ", "-").replace("_", "-")
    aliases = {
        "scifi": "sci-fi",
        "sci_fi": "sci-fi",
        "hiphop": "hip-hop",
        "hip_hop": "hip-hop",
        "lofi": "lo-fi",
        "lo_fi": "lo-fi",
    }
    key = aliases.get(key, key)
    if key not in _GENRES:
        raise ValueError(f"Unknown genre '{code}'. Register it via register_genre().")
    return key


def get_genre(code: str | None) -> GenreDef:
    return _GENRES[normalize_genre(code)]


def list_genres() -> list[dict[str, Any]]:
    return [g.to_dict() for g in sorted(_GENRES.values(), key=lambda x: x.name)]


def is_known_genre(code: str | None) -> bool:
    try:
        normalize_genre(code)
        return True
    except ValueError:
        return False

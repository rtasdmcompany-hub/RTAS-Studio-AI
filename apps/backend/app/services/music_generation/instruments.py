"""Instrument library — pluggable catalog."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class InstrumentDef:
    code: str
    name: str
    family: str
    genres: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["genres"] = list(self.genres)
        return d


_INSTRUMENTS: dict[str, InstrumentDef] = {}


def _defaults() -> None:
    items = [
        InstrumentDef("piano", "Piano", "keys", ("emotional", "sad", "romantic", "cinematic")),
        InstrumentDef("strings", "Strings", "orchestra", ("cinematic", "epic", "orchestral", "emotional")),
        InstrumentDef("brass", "Brass", "orchestra", ("epic", "action", "orchestral")),
        InstrumentDef("synth", "Synth", "electronic", ("sci-fi", "electronic", "ambient", "lo-fi")),
        InstrumentDef("drums", "Drums", "percussion", ("action", "hip-hop", "electronic", "epic")),
        InstrumentDef("guitar", "Guitar", "strings", ("acoustic", "romantic", "corporate")),
        InstrumentDef("bass", "Bass", "rhythm", ("hip-hop", "electronic", "lo-fi")),
        InstrumentDef("pads", "Pads", "atmosphere", ("ambient", "sci-fi", "documentary")),
        InstrumentDef("choir", "Choir", "vocal", ("epic", "cinematic", "horror")),
        InstrumentDef("woodwinds", "Woodwinds", "orchestra", ("documentary", "orchestral", "emotional")),
    ]
    for i in items:
        _INSTRUMENTS[i.code] = i


_defaults()


def register_instrument(inst: InstrumentDef) -> None:
    _INSTRUMENTS[inst.code.lower().strip()] = inst


def get_instrument(code: str) -> InstrumentDef:
    key = (code or "").lower().strip()
    if key not in _INSTRUMENTS:
        raise ValueError(f"Unknown instrument '{code}'")
    return _INSTRUMENTS[key]


def list_instruments() -> list[dict[str, Any]]:
    return [i.to_dict() for i in sorted(_INSTRUMENTS.values(), key=lambda x: x.name)]


def resolve_instruments(codes: list[str] | None, genre: str) -> list[str]:
    if codes:
        out = []
        for c in codes:
            key = c.lower().strip()
            if key not in _INSTRUMENTS:
                raise ValueError(f"Unknown instrument '{c}'")
            out.append(key)
        return out
    # Genre-aware defaults
    defaults: dict[str, list[str]] = {
        "cinematic": ["strings", "piano", "pads"],
        "epic": ["brass", "strings", "drums", "choir"],
        "emotional": ["piano", "strings"],
        "sad": ["piano", "strings"],
        "romantic": ["piano", "guitar", "strings"],
        "corporate": ["piano", "guitar", "pads"],
        "documentary": ["piano", "woodwinds", "pads"],
        "action": ["drums", "brass", "synth"],
        "horror": ["pads", "choir", "synth"],
        "sci-fi": ["synth", "pads", "drums"],
        "hip-hop": ["drums", "bass", "synth"],
        "lo-fi": ["piano", "drums", "bass"],
        "orchestral": ["strings", "brass", "woodwinds"],
        "electronic": ["synth", "drums", "bass"],
        "ambient": ["pads", "synth", "piano"],
        "acoustic": ["guitar", "piano"],
    }
    return list(defaults.get(genre, ["piano", "pads"]))

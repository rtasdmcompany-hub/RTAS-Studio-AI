"""Pluggable SFX / ambient category registry — unlimited future categories."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

Kind = Literal["sfx", "ambient", "foley", "both"]


@dataclass(frozen=True)
class CategoryDef:
    code: str
    name: str
    kind: Kind
    default_volume: float
    loopable: bool
    tags: tuple[str, ...] = ()
    mood_affinity: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["tags"] = list(self.tags)
        d["mood_affinity"] = list(self.mood_affinity)
        return d


_CATEGORIES: dict[str, CategoryDef] = {}


def _register_defaults() -> None:
    defaults = [
        CategoryDef("rain", "Rain", "ambient", 0.45, True, ("weather",), ("calm", "sad")),
        CategoryDef("thunder", "Thunder", "sfx", 0.8, False, ("weather",), ("tense", "dramatic")),
        CategoryDef("wind", "Wind", "ambient", 0.4, True, ("weather",), ("lonely", "calm")),
        CategoryDef("ocean", "Ocean", "ambient", 0.5, True, ("water",), ("calm", "romantic")),
        CategoryDef("river", "River", "ambient", 0.4, True, ("water",), ("peaceful",)),
        CategoryDef("waterfall", "Waterfall", "ambient", 0.55, True, ("water",), ("dramatic",)),
        CategoryDef("fire", "Fire", "ambient", 0.5, True, ("element",), ("warm", "tense")),
        CategoryDef("explosion", "Explosion", "sfx", 0.95, False, ("impact",), ("action",)),
        CategoryDef("footsteps", "Footsteps", "foley", 0.55, False, ("foley",), ("neutral",)),
        CategoryDef("birds", "Birds", "ambient", 0.35, True, ("nature",), ("peaceful", "happy")),
        CategoryDef("animals", "Animals", "sfx", 0.5, False, ("nature",), ("wild",)),
        CategoryDef("crowd", "Crowd", "ambient", 0.45, True, ("urban",), ("busy",)),
        CategoryDef("city-traffic", "City Traffic", "ambient", 0.5, True, ("urban",), ("busy",)),
        CategoryDef("market", "Market", "ambient", 0.45, True, ("urban",), ("busy", "cultural")),
        CategoryDef("office", "Office", "ambient", 0.3, True, ("interior",), ("corporate",)),
        CategoryDef("factory", "Factory", "ambient", 0.55, True, ("industrial",), ("tense",)),
        CategoryDef("nature", "Nature", "ambient", 0.4, True, ("outdoor",), ("calm",)),
        CategoryDef("forest", "Forest", "ambient", 0.4, True, ("outdoor",), ("mysterious", "calm")),
        CategoryDef("desert", "Desert", "ambient", 0.35, True, ("outdoor",), ("lonely",)),
        CategoryDef("snow", "Snow", "ambient", 0.3, True, ("weather",), ("cold", "calm")),
        CategoryDef("space", "Space", "ambient", 0.35, True, ("sci-fi",), ("awe",)),
        CategoryDef("sci-fi", "Sci-Fi", "both", 0.5, True, ("sci-fi",), ("futuristic",)),
        CategoryDef("ui-sounds", "UI Sounds", "sfx", 0.4, False, ("interface",), ("neutral",)),
        CategoryDef("mechanical", "Mechanical", "sfx", 0.55, False, ("machine",), ("industrial",)),
        CategoryDef("weapon-effects", "Weapon Effects", "sfx", 0.85, False, ("combat",), ("action",)),
    ]
    for c in defaults:
        _CATEGORIES[c.code] = c


_register_defaults()


def register_category(category: CategoryDef) -> None:
    _CATEGORIES[category.code.lower().strip()] = category


def normalize_category(code: str | None) -> str:
    key = (code or "nature").lower().strip().replace(" ", "-").replace("_", "-")
    aliases = {
        "citytraffic": "city-traffic",
        "city_traffic": "city-traffic",
        "traffic": "city-traffic",
        "uisounds": "ui-sounds",
        "ui": "ui-sounds",
        "weaponeffects": "weapon-effects",
        "weapons": "weapon-effects",
        "scifi": "sci-fi",
        "footstep": "footsteps",
    }
    key = aliases.get(key, key)
    if key not in _CATEGORIES:
        raise ValueError(f"Unknown category '{code}'. Register via register_category().")
    return key


def get_category(code: str | None) -> CategoryDef:
    return _CATEGORIES[normalize_category(code)]


def is_known_category(code: str | None) -> bool:
    try:
        normalize_category(code)
        return True
    except ValueError:
        return False


def list_categories(*, kind: str | None = None) -> list[dict[str, Any]]:
    items = sorted(_CATEGORIES.values(), key=lambda x: x.name)
    if kind:
        k = kind.lower()
        items = [c for c in items if c.kind == k or c.kind == "both" or (k == "ambient" and c.kind == "ambient")]
    return [c.to_dict() for c in items]


def recommend_for_mood(mood: str | None, *, limit: int = 5) -> list[str]:
    m = (mood or "").lower().strip()
    scored: list[tuple[float, str]] = []
    for c in _CATEGORIES.values():
        score = 0.0
        if m and m in c.mood_affinity:
            score += 2.0
        for aff in c.mood_affinity:
            if aff in m or m in aff:
                score += 1.0
        if score > 0:
            scored.append((score, c.code))
    scored.sort(key=lambda x: (-x[0], x[1]))
    if not scored:
        return ["nature", "wind", "birds"][:limit]
    return [c for _, c in scored[:limit]]

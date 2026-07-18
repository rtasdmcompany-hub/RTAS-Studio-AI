"""World / location / weather / lighting libraries — extensible."""

from __future__ import annotations

from typing import Any

_BUILTIN_ENVIRONMENTS: dict[str, dict[str, Any]] = {
    "city": {"category": "urban", "default_weather": "cloudy", "default_time": "day", "assets": ["buildings", "roads", "vehicles"]},
    "village": {"category": "rural", "default_weather": "sunny", "default_time": "day", "assets": ["houses", "dirt_roads", "trees"]},
    "forest": {"category": "nature", "default_weather": "fog", "default_time": "day", "assets": ["trees", "undergrowth", "paths"]},
    "desert": {"category": "nature", "default_weather": "sunny", "default_time": "day", "assets": ["dunes", "rocks", "haze"]},
    "mountains": {"category": "nature", "default_weather": "cloudy", "default_time": "day", "assets": ["peaks", "rocks", "trails"]},
    "snow": {"category": "nature", "default_weather": "snow", "default_time": "day", "assets": ["snowfields", "trees", "ice"]},
    "ocean": {"category": "water", "default_weather": "wind", "default_time": "day", "assets": ["waves", "horizon", "boats"]},
    "beach": {"category": "water", "default_weather": "sunny", "default_time": "golden_hour", "assets": ["sand", "palms", "shore"]},
    "river": {"category": "water", "default_weather": "cloudy", "default_time": "day", "assets": ["water", "banks", "rocks"]},
    "space": {"category": "sci_fi", "default_weather": "night", "default_time": "night", "assets": ["stars", "nebula", "stations"]},
    "office": {"category": "interior", "default_weather": "cloudy", "default_time": "day", "assets": ["desks", "screens", "windows"]},
    "home": {"category": "interior", "default_weather": "sunny", "default_time": "evening", "assets": ["furniture", "lamps", "walls"]},
    "school": {"category": "interior", "default_weather": "sunny", "default_time": "day", "assets": ["classrooms", "hallways", "boards"]},
    "hospital": {"category": "interior", "default_weather": "cloudy", "default_time": "day", "assets": ["corridors", "beds", "lights"]},
    "factory": {"category": "industrial", "default_weather": "cloudy", "default_time": "day", "assets": ["machines", "pipes", "crates"]},
    "restaurant": {"category": "interior", "default_weather": "night", "default_time": "evening", "assets": ["tables", "kitchen", "ambience"]},
    "airport": {"category": "transit", "default_weather": "cloudy", "default_time": "day", "assets": ["terminals", "runways", "planes"]},
    "hotel": {"category": "interior", "default_weather": "night", "default_time": "evening", "assets": ["lobby", "rooms", "elevators"]},
    "shopping_mall": {"category": "urban", "default_weather": "cloudy", "default_time": "day", "assets": ["stores", "escalators", "crowd"]},
    "stadium": {"category": "urban", "default_weather": "sunny", "default_time": "day", "assets": ["stands", "field", "lights"]},
    "historical": {"category": "period", "default_weather": "golden_hour", "default_time": "golden_hour", "assets": ["ruins", "stone", "flags"]},
    "futuristic": {"category": "sci_fi", "default_weather": "night", "default_time": "night", "assets": ["neon", "towers", "drones"]},
    "fantasy": {"category": "fantasy", "default_weather": "fog", "default_time": "blue_hour", "assets": ["castles", "magic", "forests"]},
    "custom": {"category": "custom", "default_weather": "sunny", "default_time": "day", "assets": ["generic"]},
}

_CUSTOM_ENVIRONMENTS: dict[str, dict[str, Any]] = {}

_WEATHER: dict[str, dict[str, Any]] = {
    "sunny": {"precip": 0.0, "visibility": 1.0, "wind": 0.15, "moods": ("happy", "motivational", "calm")},
    "cloudy": {"precip": 0.0, "visibility": 0.85, "wind": 0.25, "moods": ("serious", "calm", "emotional")},
    "rain": {"precip": 0.7, "visibility": 0.6, "wind": 0.35, "moods": ("sad", "romantic", "emotional")},
    "thunderstorm": {"precip": 0.9, "visibility": 0.4, "wind": 0.8, "moods": ("angry", "fear", "suspense")},
    "snow": {"precip": 0.6, "visibility": 0.55, "wind": 0.3, "moods": ("calm", "romantic", "sad")},
    "fog": {"precip": 0.1, "visibility": 0.35, "wind": 0.1, "moods": ("suspense", "fear", "mystery")},
    "wind": {"precip": 0.0, "visibility": 0.9, "wind": 0.75, "moods": ("excited", "action", "tense")},
    "sunset": {"precip": 0.0, "visibility": 0.95, "wind": 0.2, "moods": ("romantic", "emotional", "proud")},
    "sunrise": {"precip": 0.0, "visibility": 0.95, "wind": 0.15, "moods": ("motivational", "hopeful", "calm")},
    "night": {"precip": 0.0, "visibility": 0.5, "wind": 0.2, "moods": ("suspense", "serious", "fear")},
    "golden_hour": {"precip": 0.0, "visibility": 0.98, "wind": 0.15, "moods": ("romantic", "cinematic", "warm")},
    "blue_hour": {"precip": 0.0, "visibility": 0.8, "wind": 0.15, "moods": ("calm", "melancholy", "cinematic")},
}

_LIGHTING_STYLES: dict[str, dict[str, Any]] = {
    "natural_light": {"soft_hard": "soft", "rim": False, "hdr": True, "shadows": "soft", "gi": 0.7, "kelvin": 5600},
    "studio_light": {"soft_hard": "soft", "rim": True, "hdr": False, "shadows": "controlled", "gi": 0.4, "kelvin": 5200},
    "soft_light": {"soft_hard": "soft", "rim": False, "hdr": True, "shadows": "diffused", "gi": 0.65, "kelvin": 5400},
    "hard_light": {"soft_hard": "hard", "rim": False, "hdr": True, "shadows": "crisp", "gi": 0.5, "kelvin": 6000},
    "rim_light": {"soft_hard": "soft", "rim": True, "hdr": True, "shadows": "soft", "gi": 0.55, "kelvin": 5000},
    "cinematic_light": {"soft_hard": "mixed", "rim": True, "hdr": True, "shadows": "dramatic", "gi": 0.75, "kelvin": 4800},
    "hdr_lighting": {"soft_hard": "mixed", "rim": False, "hdr": True, "shadows": "rich", "gi": 0.9, "kelvin": 5500},
}


def register_environment(env_id: str, spec: dict[str, Any]) -> None:
    key = (env_id or "").strip().lower().replace(" ", "_").replace("-", "_")
    if not key:
        raise ValueError("env_id is required")
    _CUSTOM_ENVIRONMENTS[key] = {
        "category": spec.get("category") or "custom",
        "default_weather": spec.get("default_weather") or "sunny",
        "default_time": spec.get("default_time") or "day",
        "assets": list(spec.get("assets") or ["generic"]),
        "custom": True,
    }


def resolve_environment(env: str | None) -> str:
    key = (env or "city").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {"mall": "shopping_mall", "sea": "ocean", "woods": "forest", "sci_fi": "futuristic"}
    key = aliases.get(key, key)
    catalog = {**_BUILTIN_ENVIRONMENTS, **_CUSTOM_ENVIRONMENTS}
    if key not in catalog:
        register_environment(key, {"category": "custom"})
    return key


def resolve_weather(weather: str | None) -> str:
    key = (weather or "sunny").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {"storm": "thunderstorm", "clear": "sunny", "overcast": "cloudy", "mist": "fog"}
    key = aliases.get(key, key)
    if key not in _WEATHER:
        return "sunny"
    return key


def resolve_time(time_of_day: str | None) -> str:
    key = (time_of_day or "day").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {"dawn": "sunrise", "dusk": "sunset", "evening": "golden_hour", "midnight": "night"}
    key = aliases.get(key, key)
    valid = {"day", "night", "sunrise", "sunset", "golden_hour", "blue_hour", "evening"}
    return key if key in valid or key in _WEATHER else "day"


def get_environment_spec(env: str) -> dict[str, Any]:
    key = resolve_environment(env)
    return dict({**_BUILTIN_ENVIRONMENTS, **_CUSTOM_ENVIRONMENTS}[key])


def get_weather_spec(weather: str) -> dict[str, Any]:
    return dict(_WEATHER[resolve_weather(weather)])


def pick_lighting_for(weather: str, time_of_day: str, mood: str | None = None) -> str:
    w = resolve_weather(weather)
    t = resolve_time(time_of_day)
    m = (mood or "").lower()
    if w in ("thunderstorm", "night") or t == "night":
        return "cinematic_light"
    if w in ("golden_hour", "sunset") or t in ("golden_hour", "sunset"):
        return "rim_light"
    if w == "fog" or m in ("suspense", "fear"):
        return "soft_light"
    if m in ("serious", "angry"):
        return "hard_light"
    if t in ("sunrise", "blue_hour"):
        return "natural_light"
    return "hdr_lighting"


def list_world_library() -> dict[str, Any]:
    catalog = {**_BUILTIN_ENVIRONMENTS, **_CUSTOM_ENVIRONMENTS}
    return {
        "environments": [{"environment_id": k, **v} for k, v in sorted(catalog.items())],
        "weather": [{"weather_id": k, **v} for k, v in _WEATHER.items()],
        "lighting": [{"lighting_id": k, **v} for k, v in _LIGHTING_STYLES.items()],
        "environment_count": len(catalog),
        "weather_count": len(_WEATHER),
        "lighting_count": len(_LIGHTING_STYLES),
        "extensible": True,
    }


def get_lighting_spec(lighting_id: str) -> dict[str, Any]:
    key = (lighting_id or "natural_light").strip().lower()
    return dict(_LIGHTING_STYLES.get(key, _LIGHTING_STYLES["natural_light"]))


_MOOD_TO_WEATHER = {
    "sad": "rain",
    "romantic": "golden_hour",
    "fear": "fog",
    "suspense": "night",
    "angry": "thunderstorm",
    "happy": "sunny",
    "calm": "blue_hour",
    "motivational": "sunrise",
    "cinematic": "golden_hour",
}


def weather_for_mood(mood: str | None) -> str:
    """Synchronize weather with scene mood."""
    key = (mood or "calm").strip().lower()
    return resolve_weather(_MOOD_TO_WEATHER.get(key, "sunny"))


_MOOD_WEATHER_SYNC = {
    "sad": "rain",
    "romantic": "golden_hour",
    "fear": "fog",
    "suspense": "night",
    "angry": "thunderstorm",
    "happy": "sunny",
    "calm": "blue_hour",
    "motivational": "sunrise",
    "excited": "wind",
    "cinematic": "golden_hour",
}


def weather_for_mood(mood: str | None) -> str:
    """Automatically synchronize weather with scene mood."""
    key = (mood or "calm").strip().lower()
    return resolve_weather(_MOOD_WEATHER_SYNC.get(key, "sunny"))


_MOOD_WEATHER_SYNC = {
    "sad": "rain",
    "romantic": "golden_hour",
    "fear": "fog",
    "suspense": "night",
    "angry": "thunderstorm",
    "happy": "sunny",
    "calm": "blue_hour",
    "motivational": "sunrise",
    "excited": "wind",
    "cinematic": "golden_hour",
}


def weather_for_mood(mood: str | None) -> str:
    """Synchronize weather with scene mood."""
    key = (mood or "calm").strip().lower()
    return resolve_weather(_MOOD_WEATHER_SYNC.get(key, "sunny"))

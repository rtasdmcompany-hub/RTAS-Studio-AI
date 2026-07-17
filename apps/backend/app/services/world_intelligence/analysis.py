"""World analysis — detect environment, weather, time from scene prompt/mood."""

from __future__ import annotations

from app.services.world_intelligence.library import resolve_environment, resolve_time, resolve_weather
from app.services.world_intelligence.models import WorldAnalysis

_ENV_KEYWORDS: dict[str, tuple[str, ...]] = {
    "city": ("city", "street", "skyline", "downtown", "urban"),
    "village": ("village", "countryside", "hamlet"),
    "forest": ("forest", "woods", "jungle", "trees"),
    "desert": ("desert", "dunes", "sandstorm"),
    "mountains": ("mountain", "peak", "alpine", "cliff"),
    "snow": ("snow", "arctic", "blizzard", "winter landscape"),
    "ocean": ("ocean", "sea", "ship", "waves"),
    "beach": ("beach", "shore", "coast"),
    "river": ("river", "stream", "creek"),
    "space": ("space", "orbit", "galaxy", "spaceship"),
    "office": ("office", "cubicle", "meeting room"),
    "home": ("home", "apartment", "living room", "kitchen"),
    "school": ("school", "classroom", "campus"),
    "hospital": ("hospital", "clinic", "ward"),
    "factory": ("factory", "warehouse", "industrial"),
    "restaurant": ("restaurant", "cafe", "diner"),
    "airport": ("airport", "terminal", "runway"),
    "hotel": ("hotel", "lobby", "suite"),
    "shopping_mall": ("mall", "shopping center"),
    "stadium": ("stadium", "arena", "match"),
    "historical": ("castle", "ruins", "ancient", "temple"),
    "futuristic": ("neon", "cyber", "futuristic", "metroplex"),
    "fantasy": ("dragon", "magic", "elf", "enchanted"),
}

_WEATHER_KEYWORDS: dict[str, tuple[str, ...]] = {
    "rain": ("rain", "rainy", "drizzle"),
    "thunderstorm": ("thunder", "storm", "lightning"),
    "snow": ("snowing", "snowfall", "blizzard"),
    "fog": ("fog", "mist", "haze"),
    "wind": ("windy", "gale"),
    "sunny": ("sunny", "bright sun", "clear sky"),
    "cloudy": ("cloudy", "overcast"),
    "sunset": ("sunset", "dusk"),
    "sunrise": ("sunrise", "dawn"),
    "night": ("night", "midnight", "moonlight"),
    "golden_hour": ("golden hour", "warm glow"),
    "blue_hour": ("blue hour", "twilight"),
}

_MOOD_WEATHER = {
    "sad": "rain",
    "romantic": "golden_hour",
    "fear": "fog",
    "suspense": "night",
    "angry": "thunderstorm",
    "happy": "sunny",
    "calm": "blue_hour",
    "motivational": "sunrise",
}


def analyze_world(
    prompt: str,
    *,
    mood: str | None = None,
    environment_hint: str | None = None,
    weather_hint: str | None = None,
    time_hint: str | None = None,
) -> WorldAnalysis:
    text = (prompt or "").lower()
    env_scores = {k: 0.0 for k in _ENV_KEYWORDS}
    for env, kws in _ENV_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                env_scores[env] += 1.0
    weather_scores = {k: 0.0 for k in _WEATHER_KEYWORDS}
    for w, kws in _WEATHER_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                weather_scores[w] += 1.0

    if environment_hint:
        env = resolve_environment(environment_hint)
    else:
        best_env = max(env_scores.items(), key=lambda kv: kv[1])
        env = resolve_environment(best_env[0] if best_env[1] > 0 else "city")

    if weather_hint:
        weather = resolve_weather(weather_hint)
    else:
        best_w = max(weather_scores.items(), key=lambda kv: kv[1])
        if best_w[1] > 0:
            weather = resolve_weather(best_w[0])
        elif mood and mood.lower() in _MOOD_WEATHER:
            weather = resolve_weather(_MOOD_WEATHER[mood.lower()])
        else:
            weather = "sunny"

    if time_hint:
        tod = resolve_time(time_hint)
    elif weather in ("sunset", "sunrise", "night", "golden_hour", "blue_hour"):
        tod = weather if weather != "sunny" else "day"
        if weather == "sunset":
            tod = "sunset"
        elif weather == "sunrise":
            tod = "sunrise"
        elif weather == "night":
            tod = "night"
        elif weather == "golden_hour":
            tod = "golden_hour"
        elif weather == "blue_hour":
            tod = "blue_hour"
        else:
            tod = "day"
    else:
        tod = "day"

    peak = max(list(env_scores.values()) + list(weather_scores.values()) + [0])
    confidence = min(0.98, 0.5 + peak * 0.15)
    notes = [f"environment={env}", f"weather={weather}", f"time={tod}"]
    if mood:
        notes.append(f"mood_sync={mood}")

    return WorldAnalysis(
        scene_type=env,
        recommended_environment=env,
        recommended_weather=weather,
        recommended_time=tod,
        mood=(mood or "calm").lower(),
        confidence=round(confidence, 3),
        notes=notes,
    )

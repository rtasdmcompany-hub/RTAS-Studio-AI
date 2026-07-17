"""Environment / weather / lighting / time builders."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.world_intelligence.library import (
    get_environment_spec,
    get_lighting_spec,
    get_weather_spec,
    pick_lighting_for,
    resolve_environment,
    resolve_time,
    resolve_weather,
)
from app.services.world_intelligence.models import (
    EnvironmentBlueprint,
    LightingProfile,
    WeatherProfile,
)


def build_weather(weather_id: str, *, intensity: float = 0.6, mood: str = "calm") -> WeatherProfile:
    wid = resolve_weather(weather_id)
    spec = get_weather_spec(wid)
    return WeatherProfile(
        weather_id=wid,
        mood_sync=mood,
        intensity=max(0.1, min(1.0, intensity)),
        precipitation=float(spec.get("precip", 0.0)),
        visibility=float(spec.get("visibility", 1.0)),
        wind=float(spec.get("wind", 0.2)),
    )


def build_lighting(lighting_id: str) -> LightingProfile:
    lid = (lighting_id or "natural_light").strip().lower()
    spec = get_lighting_spec(lid)
    return LightingProfile(
        lighting_id=lid if lid in (
            "natural_light", "studio_light", "soft_light", "hard_light",
            "rim_light", "cinematic_light", "hdr_lighting",
        ) else "natural_light",
        style=lid,
        soft_hard=str(spec.get("soft_hard", "soft")),
        rim=bool(spec.get("rim", False)),
        hdr=bool(spec.get("hdr", True)),
        shadows=str(spec.get("shadows", "soft")),
        reflections=0.55 if spec.get("hdr") else 0.35,
        gi_strength=float(spec.get("gi", 0.6)),
        color_temp_k=int(spec.get("kelvin", 5500)),
    )


def build_environment(
    *,
    world_id: str,
    environment: str,
    weather: str,
    time_of_day: str,
    mood: str = "calm",
    lighting_override: str | None = None,
) -> EnvironmentBlueprint:
    env = resolve_environment(environment)
    spec = get_environment_spec(env)
    wid = resolve_weather(weather)
    tod = resolve_time(time_of_day)
    lighting_id = lighting_override or pick_lighting_for(wid, tod, mood)
    loc_digest = hashlib.sha1(f"{world_id}|{env}".encode()).hexdigest()[:10]
    assets = {
        "buildings": "buildings" in spec.get("assets", []),
        "roads": any(a in spec.get("assets", []) for a in ("roads", "dirt_roads", "paths", "trails")),
        "trees": "trees" in spec.get("assets", []) or "palms" in spec.get("assets", []),
        "background_objects": list(spec.get("assets") or []),
        "sky": "clear" if wid == "sunny" else "overcast" if wid == "cloudy" else wid,
        "environmental_assets": list(spec.get("assets") or []),
    }
    sky = assets["sky"]
    return EnvironmentBlueprint(
        environment_id=env,
        location_id=f"loc_{loc_digest}",
        category=str(spec.get("category") or "custom"),
        assets=assets,
        sky=str(sky),
        time_of_day=tod,
        weather=build_weather(wid, mood=mood),
        lighting=build_lighting(lighting_id),
    )

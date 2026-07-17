"""Lighting setup for scene rendering."""

from __future__ import annotations

from typing import Any

from app.services.scene_render.models import LightingSetup


def build_lighting(
    text: str,
    *,
    visual_style: dict[str, Any] | None = None,
    prompt_understanding: dict[str, Any] | None = None,
    environment: str | None = None,
) -> LightingSetup:
    vs = visual_style or {}
    pu = prompt_understanding or {}
    blob = " ".join(
        [
            text or "",
            str(vs.get("lighting") or ""),
            str(pu.get("lighting") or ""),
            environment or "",
            str(pu.get("time_of_day") or pu.get("time") or ""),
        ]
    ).lower()

    key = "soft key 45°"
    fill = "soft fill −1.5 stops"
    rim = "subtle rim"
    ambient = "neutral ambient occlusion"
    practicals: list[str] = []
    temp = 5600
    intensity = 0.7
    volumetric = False
    notes: list[str] = []

    if any(x in blob for x in ("night", "noir", "moon", "dark")):
        key = "hard cool key"
        fill = "deep fill −2.5 stops"
        rim = "cyan rim accent"
        ambient = "low ambient; crushed blacks controlled"
        temp = 4200
        intensity = 0.55
        notes.append("night exposure — protect highlights on practicals")
    elif any(x in blob for x in ("golden hour", "sunset", "sunrise", "warm")):
        key = "warm low-angle key"
        fill = "warm bounce fill"
        rim = "orange rim"
        temp = 3200
        intensity = 0.75
        notes.append("golden-hour warmth; gentle falloff")
    elif any(x in blob for x in ("overcast", "soft", "diffuse")):
        key = "broad soft key"
        fill = "even fill"
        rim = "minimal rim"
        temp = 6500
        intensity = 0.65
    elif any(x in blob for x in ("harsh", "desert", "noon", "hard sun")):
        key = "hard overhead sun"
        fill = "minimal fill"
        rim = "strong edge"
        temp = 5800
        intensity = 0.9
        notes.append("hard sunlight — tight shadow control")

    if any(x in blob for x in ("rain", "fog", "smoke", "dust", "volumetric", "god ray")):
        volumetric = True
        notes.append("enable volumetric scattering for atmosphere")

    if any(x in blob for x in ("neon", "city", "club", "practical")):
        practicals = ["neon practicals", "window spill"]
        notes.append("practical-motivated lighting")
    elif "interior" in blob or "room" in blob:
        practicals = ["practical lamp", "window key"]

    style_light = str(vs.get("lighting") or "").strip()
    if style_light:
        notes.append(f"visual style lighting: {style_light}")

    return LightingSetup(
        key=key,
        fill=fill,
        rim=rim,
        ambient=ambient,
        practicals=practicals,
        color_temperature_k=temp,
        intensity=round(intensity, 3),
        volumetric=volumetric,
        notes=notes,
    )

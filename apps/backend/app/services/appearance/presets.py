"""Style Preset Engine — reusable cinematic / commercial looks."""

from __future__ import annotations

from typing import Any

from app.services.appearance.models import StylePreset, StylePresetId

_PRESETS: dict[str, StylePreset] = {
    "cinematic": StylePreset(
        preset_id="cinematic",
        name="Cinematic",
        description="Film-grade contrast, shallow depth, dramatic framing",
        look={"contrast": "high", "grain": "subtle", "lens": "anamorphic"},
        lighting="motivated_key",
        color_grade="teal_orange",
        camera="35mm_cinematic",
    ),
    "realistic": StylePreset(
        preset_id="realistic",
        name="Realistic",
        description="Natural everyday look with balanced tones",
        look={"contrast": "medium", "grain": "none", "lens": "prime"},
        lighting="soft_natural",
        color_grade="neutral",
        camera="50mm_standard",
    ),
    "hyper_realistic": StylePreset(
        preset_id="hyper_realistic",
        name="Hyper Realistic",
        description="Ultra-detailed skin pores and fabric micro-texture",
        look={"contrast": "medium_high", "detail": "extreme", "lens": "macro_ready"},
        lighting="studio_softbox",
        color_grade="true_to_life",
        camera="85mm_portrait",
    ),
    "luxury": StylePreset(
        preset_id="luxury",
        name="Luxury",
        description="Premium fashion polish with elegant highlights",
        look={"contrast": "soft_high", "sheen": "satin", "lens": "portrait"},
        lighting="beauty_rim",
        color_grade="warm_gold",
        camera="85mm_luxury",
    ),
    "documentary": StylePreset(
        preset_id="documentary",
        name="Documentary",
        description="Observational handheld realism",
        look={"contrast": "medium", "grain": "light", "lens": "zoom"},
        lighting="available_light",
        color_grade="desaturated",
        camera="28mm_doc",
    ),
    "commercial": StylePreset(
        preset_id="commercial",
        name="Commercial",
        description="Clean product/brand advertising finish",
        look={"contrast": "crisp", "clarity": "high", "lens": "standard"},
        lighting="bright_even",
        color_grade="vivid_clean",
        camera="35mm_commercial",
    ),
    "music_video": StylePreset(
        preset_id="music_video",
        name="Music Video",
        description="Stylized color pops and dynamic motion cues",
        look={"contrast": "stylized", "motion": "kinetic", "lens": "wide_tele"},
        lighting="colored_gels",
        color_grade="neon_pop",
        camera="24mm_mv",
    ),
    "action": StylePreset(
        preset_id="action",
        name="Action",
        description="High energy, punchy contrast, motion clarity",
        look={"contrast": "punchy", "sharpen": "high", "lens": "wide"},
        lighting="hard_directional",
        color_grade="cool_steel",
        camera="24mm_action",
    ),
    "fashion": StylePreset(
        preset_id="fashion",
        name="Fashion",
        description="Editorial runway and lookbook styling",
        look={"contrast": "editorial", "pose": "strong", "lens": "tele"},
        lighting="fashion_flash",
        color_grade="magazine",
        camera="70mm_fashion",
    ),
}


def list_presets() -> list[StylePreset]:
    return list(_PRESETS.values())


def get_preset(preset_id: str | None) -> StylePreset | None:
    if not preset_id:
        return None
    key = preset_id.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "hyperrealistic": "hyper_realistic",
        "hyper": "hyper_realistic",
        "musicvideo": "music_video",
        "mv": "music_video",
        "doc": "documentary",
        "ad": "commercial",
    }
    key = aliases.get(key, key)
    return _PRESETS.get(key)


def resolve_preset_id(preset_id: str | None) -> StylePresetId | None:
    preset = get_preset(preset_id)
    return preset.preset_id if preset else None


def preset_payload(preset_id: str | None = None) -> dict[str, Any]:
    if preset_id:
        preset = get_preset(preset_id)
        if not preset:
            raise ValueError(f"Unknown style preset: {preset_id}")
        return {"preset": preset.to_dict(), "presets": [p.to_dict() for p in list_presets()]}
    return {"presets": [p.to_dict() for p in list_presets()], "count": len(_PRESETS)}

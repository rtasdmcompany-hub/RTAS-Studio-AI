"""Build locked face features from character identity / overrides."""

from __future__ import annotations

from typing import Any

from app.services.face_lock.models import FaceFeatures


def features_from_character(character: dict[str, Any] | None = None) -> FaceFeatures:
    c = character or {}
    identity = c.get("identity") if isinstance(c.get("identity"), dict) else c
    age = identity.get("age") or c.get("age") or 28
    try:
        age_i = int(age)
    except (TypeError, ValueError):
        age_i = 28
    hairstyle = str(identity.get("hairstyle") or c.get("hairstyle") or "short")
    beard = str(identity.get("beard") or c.get("beard") or "none")
    skin = str(identity.get("skin") or identity.get("skin_tone") or c.get("skin") or "medium")
    body = str(
        identity.get("body_type")
        or identity.get("body_proportions")
        or c.get("body_type")
        or "average"
    )
    eye = str(identity.get("eye_color") or c.get("eye_color") or "brown")
    return FaceFeatures(
        face_structure=str(c.get("face_structure") or f"oval_{skin}"),
        eye_shape=str(c.get("eye_shape") or f"almond_{eye}"),
        nose=str(c.get("nose") or "balanced"),
        lips=str(c.get("lips") or "medium"),
        jawline=str(c.get("jawline") or "soft"),
        ears=str(c.get("ears") or "proportional"),
        hairstyle=hairstyle,
        beard=beard,
        age=max(1, min(120, age_i)),
        skin_tone=skin,
        body_proportions=body,
    )


def features_from_overrides(base: FaceFeatures, overrides: dict[str, Any] | None) -> FaceFeatures:
    if not overrides:
        return base
    data = base.to_dict()
    for key in data:
        if key in overrides and overrides[key] is not None:
            data[key] = overrides[key]
    if "age" in data:
        data["age"] = int(data["age"])
    return FaceFeatures(**data)

"""Prompt merge — motion text + image preservation locks."""

from __future__ import annotations

from typing import Any

from app.services.image_to_video.models import ImageAsset


def _role_instruction(role: str) -> str:
    return {
        "single": "Animate the primary still into natural cinematic motion.",
        "multiple": "Bridge sequence frames with continuous motion continuity.",
        "reference": "Match reference look for style and world details.",
        "character": "Lock facial identity, hair, skin tone, and wardrobe from character reference.",
        "product": "Keep product shape, logo placement, materials, and branding exact.",
        "logo": "Preserve logo geometry, colors, and readability; no warping.",
    }.get(role, "Respect reference image fidelity.")


def merge_i2v_prompt(
    *,
    motion_prompt: str,
    images: list[ImageAsset],
    scene: dict[str, Any] | None = None,
    shot: dict[str, Any] | None = None,
    character_memory: list[dict[str, Any]] | None = None,
    preserve_identity: bool = True,
    preserve_lighting: bool = True,
    preserve_composition: bool = True,
    preserve_environment: bool = True,
    director_notes: list[str] | None = None,
) -> str:
    scene = scene or {}
    shot = shot or {}
    parts: list[str] = []

    base = (motion_prompt or "").strip()
    if base:
        parts.append(base)

    if shot.get("shot_type") or shot.get("camera_movement"):
        parts.append(
            f"Shot: {shot.get('shot_type') or 'Medium Shot'}; "
            f"movement={shot.get('camera_movement') or 'subtle parallax'}."
        )
    purpose = shot.get("purpose") or scene.get("scene_purpose") or scene.get("title")
    if purpose:
        parts.append(f"Purpose: {purpose}.")

    roles_seen = sorted({i.role for i in images})
    for role in roles_seen:
        parts.append(_role_instruction(role))

    preserve_bits = []
    if preserve_identity:
        preserve_bits.append("identity (face/body/wardrobe)")
    if preserve_lighting:
        preserve_bits.append("lighting direction and contrast from source image")
    if preserve_composition:
        preserve_bits.append("composition and framing")
    if preserve_environment:
        preserve_bits.append("environment / background continuity")
    if preserve_bits:
        parts.append("Preserve: " + "; ".join(preserve_bits) + ".")

    env = shot.get("environment") or scene.get("environment")
    weather = shot.get("weather") or scene.get("weather")
    time_of_day = shot.get("time") or scene.get("time")
    if env or weather or time_of_day:
        parts.append(
            f"World continuity: environment={env or 'as in image'}; "
            f"weather={weather or 'as in image'}; time={time_of_day or 'as in image'}."
        )

    if character_memory:
        c = character_memory[0]
        parts.append(
            f"IDENTITY LOCK [{c.get('character_id') or 'lead'}]: "
            f"{c.get('gender')}, {c.get('hair')} hair, outfit={c.get('outfit')}. "
            "Exact face match to character reference."
        )

    if any(i.role == "product" for i in images):
        parts.append("Product must remain sharp, correctly proportioned, brand-safe.")
    if any(i.role == "logo" for i in images):
        parts.append("Logo must stay legible with no distortion.")

    if director_notes:
        parts.append("Director: " + "; ".join(director_notes[:3]) + ".")

    parts.append(
        "Image-to-video: natural micro-motion, temporal consistency, "
        "no morphing, no text overlays, no watermark."
    )
    return " ".join(p for p in parts if p).strip()[:2000]


def build_negative_prompt(*, preserve_identity: bool = True) -> str:
    base = (
        "blurry, warped logo, product deformation, flicker, watermark, "
        "burned-in subtitles, low resolution"
    )
    if preserve_identity:
        base = "face morphing, identity drift, extra limbs, " + base
    return base

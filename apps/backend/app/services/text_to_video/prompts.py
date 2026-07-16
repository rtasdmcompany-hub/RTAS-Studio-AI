"""Build provider-ready prompts from scene/shot + character/director context."""

from __future__ import annotations

from typing import Any


def _join(items: list[Any] | None, sep: str = ", ") -> str:
    if not items:
        return ""
    return sep.join(str(x) for x in items if x)


def identity_lock_from_memory(
    character_memory: list[dict[str, Any]] | None,
) -> str:
    if not character_memory:
        return ""
    parts = []
    for c in character_memory:
        cid = c.get("character_id") or "lead"
        if c.get("identity_lock_prompt"):
            parts.append(str(c["identity_lock_prompt"]))
            continue
        parts.append(
            f"IDENTITY LOCK [{cid}]: gender={c.get('gender')}, age={c.get('age')}, "
            f"hair={c.get('hair')}, outfit={c.get('outfit')}, "
            f"face={c.get('face_shape')}, eyes={c.get('eye_color')}. "
            "Keep identical face, hair, clothing across shots."
        )
    return " ".join(parts)


def build_shot_prompt(
    *,
    base_prompt: str,
    shot: dict[str, Any],
    scene: dict[str, Any] | None = None,
    character_memory: list[dict[str, Any]] | None = None,
    director_notes: list[str] | None = None,
    visual_style: dict[str, Any] | None = None,
) -> str:
    scene = scene or {}
    shot_type = shot.get("shot_type") or shot.get("title") or "Medium Shot"
    movement = shot.get("camera_movement") or shot.get("movement") or "static"
    angle = shot.get("camera_angle") or shot.get("angle") or "Eye Level"
    lens = shot.get("lens") or "35mm narrative"
    lighting = _join(shot.get("lighting") or scene.get("lighting"))
    palette = _join(shot.get("color_palette") or scene.get("color_palette"))
    env = shot.get("environment") or scene.get("environment") or ""
    weather = shot.get("weather") or scene.get("weather") or ""
    time_of_day = shot.get("time") or scene.get("time") or ""
    emotion = (
        shot.get("character_emotion")
        or scene.get("character_emotion")
        or ""
    )
    expression = shot.get("facial_expression") or ""
    body = shot.get("body_language") or ""
    purpose = shot.get("purpose") or scene.get("scene_purpose") or scene.get("purpose") or ""
    composition = shot.get("composition") or ""
    dof = shot.get("depth_of_field") or ""

    style_bits = []
    if visual_style:
        if visual_style.get("reference_look"):
            style_bits.append(f"look={visual_style['reference_look']}")
        if visual_style.get("lighting"):
            style_bits.append(f"grade lighting={visual_style['lighting']}")
        if visual_style.get("color_palette"):
            style_bits.append(f"palette={_join(visual_style['color_palette'])}")

    parts = [
        (base_prompt or "").strip(),
        f"Shot: {shot_type}. Camera: {angle}, {lens}, movement={movement}.",
    ]
    if purpose:
        parts.append(f"Purpose: {purpose}.")
    if env or weather or time_of_day:
        parts.append(
            f"World: environment={env}; weather={weather}; time={time_of_day}."
        )
    if lighting:
        parts.append(f"Lighting: {lighting}.")
    if palette:
        parts.append(f"Color: {palette}.")
    if emotion or expression or body:
        parts.append(
            f"Performance: emotion={emotion}; face={expression}; body={body}."
        )
    if composition or dof:
        parts.append(f"Frame: {composition}; DOF={dof}.")
    if style_bits:
        parts.append("Visual style: " + "; ".join(style_bits) + ".")
    if director_notes:
        parts.append("Director: " + "; ".join(director_notes[:3]) + ".")

    lock = identity_lock_from_memory(character_memory)
    if lock:
        parts.append(lock)

    parts.append(
        "Cinematic photoreal motion, consistent character identity, "
        "no text overlays, no watermark."
    )
    return " ".join(p for p in parts if p).strip()[:2000]


def build_negative_prompt(shot: dict[str, Any] | None = None) -> str:
    base = (
        "blurry, deformed face, identity drift, extra limbs, watermark, "
        "subtitles burned in, low resolution, flicker"
    )
    weather = str((shot or {}).get("weather") or "").lower()
    if weather == "rain":
        base += ", dry pavement inconsistency"
    return base

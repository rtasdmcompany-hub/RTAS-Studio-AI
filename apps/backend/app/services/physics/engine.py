"""
Physics Engine.

Realistic hair, cloth, rain, smoke, dust, wind, explosion, water, fire,
particle simulation, and gravity — integrated with Director, Scene Planner,
and Motion Intelligence.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any
from uuid import uuid4

from app.services.physics.bridge import (
    build_director_integration,
    build_motion_integration,
    build_scene_planner_integration,
    locomotion_for_scene,
    resolve_scenes,
    scene_directives,
    weather_from_context,
)
from app.services.physics.catalog import DISPLAY_NAME, EFFECT_KINDS, display
from app.services.physics.detector import detect_effects
from app.services.physics.effects import build_effect_cue, flatten_timeline
from app.services.physics.forces import build_gravity, build_wind
from app.services.physics.models import PhysicsEffectKind, PhysicsPlan, ScenePhysicsPlan
from app.services.physics.store import get_plan as store_get
from app.services.physics.store import put_plan

logger = logging.getLogger(__name__)


def _job_id(prompt: str) -> str:
    seed = f"{prompt}|{uuid4().hex[:8]}"
    return f"physics_{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:10]}"


def _scene_text(scene: dict[str, Any], prompt: str) -> str:
    actions = scene.get("actions") or []
    if isinstance(actions, list):
        act = " ".join(str(a) for a in actions if a)
    else:
        act = str(actions)
    parts = [
        str(scene.get("title") or ""),
        str(scene.get("description") or ""),
        str(scene.get("environment") or ""),
        act,
    ]
    local = " ".join(p for p in parts if p).strip()
    if len(local) < 12:
        return (local + " " + (prompt or "")).strip()
    return local


def _scene_duration(scene: dict[str, Any], fallback: float) -> float:
    for key in ("duration_seconds", "duration", "Duration"):
        val = scene.get(key)
        if val is not None:
            try:
                return max(1.0, float(val))
            except (TypeError, ValueError):
                pass
    return fallback


def _scene_index(scene: dict[str, Any], i: int) -> int:
    for key in ("index", "scene_index", "SceneIndex"):
        if scene.get(key) is not None:
            try:
                return int(scene[key])
            except (TypeError, ValueError):
                pass
    return i


def _intensity_for(
    kind: PhysicsEffectKind,
    score: float,
    director_plan: dict[str, Any] | None,
) -> float:
    base = min(1.0, max(0.25, score))
    rhythm = str((director_plan or {}).get("cinematic_rhythm") or "").lower()
    if any(x in rhythm for x in ("intense", "rising", "epic")):
        if kind in ("explosion", "fire", "wind", "rain"):
            base = min(1.0, base + 0.12)
    return round(base, 3)


def build_physics_plan(
    prompt: str,
    *,
    scenes: list[dict[str, Any]] | None = None,
    director_plan: dict[str, Any] | None = None,
    scene_breakdown: dict[str, Any] | None = None,
    production_package: dict[str, Any] | None = None,
    prompt_understanding: dict[str, Any] | None = None,
    motion_intelligence: dict[str, Any] | None = None,
    character_memory: list[dict[str, Any]] | None = None,
    duration_seconds: float | None = None,
    parent_generation_id: str | None = None,
) -> PhysicsPlan:
    text = (prompt or "").strip() or "Natural outdoor scene with subtle wind."
    scene_list = resolve_scenes(scenes, scene_breakdown, production_package)
    dp = director_plan or {}
    pu = prompt_understanding or {}

    if not scene_list:
        scene_list = [
            {
                "index": 0,
                "title": "Physics Beat",
                "description": text,
                "duration_seconds": float(duration_seconds or 8.0),
                "actions": [],
                "environment": str(pu.get("weather") or ""),
            }
        ]

    default_dur = float(duration_seconds or 6.0)
    if len(scene_list) > 1 and duration_seconds:
        default_dur = max(2.0, float(duration_seconds) / len(scene_list))

    # Characters imply soft-body defaults
    has_chars = bool(character_memory) or any(
        (s.get("characters") or []) for s in scene_list
    )

    low_g = "zero g" in text.lower() or "weightless" in text.lower()
    global_gravity = build_gravity(strength=1.0, low_gravity=low_g)

    scene_plans: list[ScenePhysicsPlan] = []
    for i, scene in enumerate(scene_list):
        idx = _scene_index(scene, i)
        dur = _scene_duration(scene, default_dur)
        blob = _scene_text(scene, text)
        actions = scene.get("actions") if isinstance(scene.get("actions"), list) else []
        weather = weather_from_context(pu, scene)
        loco = locomotion_for_scene(motion_intelligence, idx)

        detected = detect_effects(
            blob,
            weather=weather,
            environment=str(scene.get("environment") or ""),
            actions=[str(a) for a in (actions or [])],
            prompt_understanding=pu,
            always_soft_body=has_chars or True,
        )

        # Ensure soft body when character memory present
        kinds_scores = {k: s for k, s in detected}
        if has_chars:
            kinds_scores["hair_motion"] = max(kinds_scores.get("hair_motion", 0.0), 0.5)
            kinds_scores["cloth_motion"] = max(kinds_scores.get("cloth_motion", 0.0), 0.5)
        kinds_scores["gravity"] = max(kinds_scores.get("gravity", 0.0), 0.4)

        # Wind field if wind/rain/storm or soft-body needs air
        need_wind = (
            kinds_scores.get("wind", 0) >= 0.45
            or kinds_scores.get("rain", 0) >= 0.7
            or kinds_scores.get("dust", 0) >= 0.7
            or "storm" in (weather or "").lower()
        )
        wind_intensity = max(
            kinds_scores.get("wind", 0.0),
            0.45 if need_wind else 0.2,
        )
        wind_field = None
        if need_wind or kinds_scores.get("hair_motion", 0) >= 0.5:
            wind_field = build_wind(
                blob,
                intensity=wind_intensity,
                storm="storm" in blob.lower() or "storm" in (weather or "").lower(),
            )
            kinds_scores["wind"] = max(kinds_scores.get("wind", 0.0), 0.5)

        active: list[PhysicsEffectKind] = [
            k
            for k, s in sorted(kinds_scores.items(), key=lambda kv: kv[1], reverse=True)
            if s >= 0.45
        ]
        # Cap to keep plans focused but always keep gravity
        if "gravity" not in active:
            active.append("gravity")
        if len(active) > 8:
            # Prefer mission-critical effects
            priority = [
                "explosion",
                "fire",
                "rain",
                "water",
                "smoke",
                "wind",
                "hair_motion",
                "cloth_motion",
                "dust",
                "particles",
                "gravity",
            ]
            active = [k for k in priority if k in active][:8]

        cues = []
        for kind in active:
            cues.append(
                build_effect_cue(
                    kind,
                    duration_seconds=dur,
                    intensity=_intensity_for(kind, kinds_scores.get(kind, 0.5), dp),
                    text=blob,
                    scene_index=idx,
                    wind_field=wind_field,
                    gravity_field=global_gravity,
                    locomotion=loco,
                )
            )

        sp = ScenePhysicsPlan(
            scene_index=idx,
            title=str(scene.get("title") or f"Scene {idx}"),
            duration_seconds=dur,
            active_effects=active,
            cues=cues,
            gravity=global_gravity,
            wind=wind_field,
        )
        sp.directives = scene_directives(sp)
        scene_plans.append(sp)

    timeline = flatten_timeline(scene_plans)
    total = sum(s.duration_seconds for s in scene_plans)

    systems = 0
    particle_names: list[str] = []
    for s in scene_plans:
        for c in s.cues:
            systems += len(c.particles)
            particle_names.extend(p.name for p in c.particles)

    provider_directives = [
        "PHYSICS ENGINE — realistic dynamics; respect gravity and collisions.",
        "Supported: Hair, Cloth, Rain, Smoke, Dust, Wind, Explosion, Water, Fire, Particles, Gravity.",
        "Secondary motion: hair/cloth follow locomotion and wind; no stiff frozen fabric.",
        "Particles: match intensity to emotion/weather; avoid overdraw clutter.",
    ]
    for s in scene_plans[:8]:
        provider_directives.append(
            f"Scene {s.scene_index}: {', '.join(display(e) for e in s.active_effects)}"
        )

    plan = PhysicsPlan(
        job_id=_job_id(text),
        prompt=text[:2000],
        total_duration_seconds=round(total, 3),
        scenes=scene_plans,
        global_gravity=global_gravity,
        timeline=timeline,
        particle_summary={
            "systems": systems,
            "names": sorted(set(particle_names))[:24],
            "supported_effects": list(EFFECT_KINDS),
            "display_names": dict(DISPLAY_NAME),
        },
        director_integration=build_director_integration(dp, scene_plans),
        scene_planner_integration=build_scene_planner_integration(
            scene_list, scene_breakdown
        ),
        motion_integration=build_motion_integration(motion_intelligence, scene_plans),
        provider_directives=provider_directives,
    )
    if parent_generation_id:
        plan.director_integration["parent_generation_id"] = parent_generation_id

    put_plan(plan)
    logger.info(
        "physics_ready job=%s scenes=%s effects=%s particles=%s",
        plan.job_id,
        len(plan.scenes),
        plan.summary().get("effects"),
        systems,
    )
    return plan


def build_physics_dict(prompt: str, **kwargs: Any) -> dict[str, Any]:
    plan = build_physics_plan(prompt, **kwargs)
    return {"plan": plan.to_dict(), "summary": plan.summary()}


def get_plan(job_id: str) -> PhysicsPlan | None:
    return store_get(job_id)

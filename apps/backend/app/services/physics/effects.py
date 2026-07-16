"""Build per-effect physics cues: particles, fluids, soft body, impulses."""

from __future__ import annotations

from typing import Any

from app.services.physics.catalog import display, spec
from app.services.physics.forces import (
    build_buoyancy,
    build_drag,
    build_explosion_impulse,
    build_gravity,
    build_wind,
)
from app.services.physics.models import (
    ForceField,
    ParticleSystem,
    PhysicsCue,
    PhysicsEffectKind,
)
from app.services.physics.soft_body import build_cloth_sim, build_hair_sim


def _particle(
    name: str,
    *,
    emitter: str,
    count: int,
    lifetime: float,
    size: float,
    velocity: tuple[float, float, float],
    spread: float,
    gravity_scale: float,
    drag: float,
    color: str,
    collision: bool = True,
) -> ParticleSystem:
    return ParticleSystem(
        name=name,
        emitter=emitter,
        count=count,
        lifetime_sec=lifetime,
        size=size,
        velocity=velocity,
        spread=spread,
        gravity_scale=gravity_scale,
        drag=drag,
        color_hint=color,
        collision=collision,
    )


def build_effect_cue(
    kind: PhysicsEffectKind,
    *,
    duration_seconds: float,
    intensity: float,
    text: str,
    scene_index: int,
    wind_field: ForceField | None,
    gravity_field: ForceField,
    locomotion: str | None = None,
) -> PhysicsCue:
    dur = max(1.0, float(duration_seconds or 4.0))
    wind_s = wind_field.strength if wind_field else 0.2
    forces: list[ForceField] = [gravity_field]
    particles: list[ParticleSystem] = []
    soft = None
    params: dict[str, Any] = {"category": spec(kind).get("category")}

    if kind == "gravity":
        params["g"] = gravity_field.vector[1]
        notes = "baseline gravity for all dynamic sims"
    elif kind == "wind":
        w = wind_field or build_wind(text, intensity=intensity)
        forces = [gravity_field, w, build_drag(intensity=0.3)]
        notes = f"wind field — {w.notes}"
        params["direction"] = list(w.vector)
    elif kind == "hair_motion":
        soft = build_hair_sim(
            wind_strength=wind_s, locomotion=locomotion, intensity=intensity
        )
        if wind_field:
            forces.append(wind_field)
        notes = soft.notes
    elif kind == "cloth_motion":
        soft = build_cloth_sim(
            wind_strength=wind_s, locomotion=locomotion, intensity=intensity
        )
        if wind_field:
            forces.append(wind_field)
        notes = soft.notes
    elif kind == "rain":
        count = int(800 + intensity * 2200)
        particles.append(
            _particle(
                "rain_streaks",
                emitter="volume",
                count=count,
                lifetime=1.2,
                size=0.02,
                velocity=(0.0, -8.0 - intensity * 4.0, 0.0),
                spread=0.15,
                gravity_scale=1.1,
                drag=0.05,
                color="cool grey streaks",
            )
        )
        if wind_field:
            forces.append(wind_field)
        params["wet_surfaces"] = True
        notes = "gravity-dominant rain; wind slant if present"
    elif kind == "smoke":
        particles.append(
            _particle(
                "smoke_plume",
                emitter="volume",
                count=int(200 + intensity * 600),
                lifetime=3.5,
                size=0.35,
                velocity=(0.0, 0.8 + intensity, 0.1),
                spread=0.55,
                gravity_scale=-0.15,
                drag=0.55,
                color="soft grey volumetric",
                collision=False,
            )
        )
        forces.extend([build_buoyancy(intensity=0.45 + intensity * 0.3), build_drag(intensity=0.5)])
        notes = "buoyant smoke with turbulence"
    elif kind == "dust":
        particles.append(
            _particle(
                "dust_motes",
                emitter="volume",
                count=int(150 + intensity * 500),
                lifetime=2.8,
                size=0.04,
                velocity=(wind_s * 0.5, 0.05, 0.2),
                spread=0.7,
                gravity_scale=0.15,
                drag=0.7,
                color="warm particulate",
                collision=False,
            )
        )
        if wind_field:
            forces.append(wind_field)
        notes = "suspended dust / kicked particulate"
    elif kind == "water":
        particles.append(
            _particle(
                "water_splash",
                emitter="surface",
                count=int(120 + intensity * 400),
                lifetime=1.4,
                size=0.08,
                velocity=(0.0, 1.5 + intensity, 0.3),
                spread=0.5,
                gravity_scale=1.0,
                drag=0.25,
                color="clear / foam white",
            )
        )
        forces.append(build_buoyancy(intensity=0.25))
        params["surface"] = "liquid"
        params["refraction"] = True
        notes = "liquid surface + splash foam"
    elif kind == "fire":
        particles.append(
            _particle(
                "fire_flames",
                emitter="point",
                count=int(180 + intensity * 500),
                lifetime=0.9,
                size=0.18,
                velocity=(0.0, 2.0 + intensity * 2.0, 0.0),
                spread=0.35,
                gravity_scale=-0.4,
                drag=0.2,
                color="orange-yellow core",
                collision=False,
            )
        )
        particles.append(
            _particle(
                "fire_embers",
                emitter="point",
                count=int(40 + intensity * 120),
                lifetime=1.6,
                size=0.03,
                velocity=(0.1, 1.2, 0.1),
                spread=0.6,
                gravity_scale=0.2,
                drag=0.15,
                color="ember orange",
                collision=False,
            )
        )
        forces.extend([build_buoyancy(intensity=0.7), build_drag(intensity=0.25)])
        notes = "combustion plume + ember particles"
    elif kind == "explosion":
        impulse = build_explosion_impulse(intensity=intensity)
        forces.extend([impulse, build_drag(intensity=0.2)])
        particles.append(
            _particle(
                "explosion_debris",
                emitter="point",
                count=int(300 + intensity * 900),
                lifetime=1.8,
                size=0.12,
                velocity=(0.0, 4.0 + intensity * 5.0, 0.0),
                spread=1.0,
                gravity_scale=1.0,
                drag=0.15,
                color="debris / fire flash",
            )
        )
        particles.append(
            _particle(
                "explosion_smoke",
                emitter="point",
                count=int(200 + intensity * 500),
                lifetime=3.0,
                size=0.5,
                velocity=(0.0, 1.5, 0.0),
                spread=0.9,
                gravity_scale=-0.1,
                drag=0.5,
                color="dark smoke",
                collision=False,
            )
        )
        params["impulse"] = True
        params["shockwave"] = round(intensity, 3)
        notes = "radial blast + debris + smoke"
    else:  # particles generic
        particles.append(
            _particle(
                "generic_particles",
                emitter="volume",
                count=int(100 + intensity * 400),
                lifetime=2.0,
                size=0.06,
                velocity=(0.0, 0.5, 0.0),
                spread=0.5,
                gravity_scale=0.6,
                drag=0.35,
                color="neutral",
            )
        )
        notes = "generic particle simulation layer"

    return PhysicsCue(
        start_sec=0.0,
        end_sec=round(dur, 3),
        kind=kind,
        intensity=round(min(1.0, max(0.1, intensity)), 3),
        forces=forces,
        particles=particles,
        soft_body=soft,
        params=params,
        notes=f"{display(kind)} — {notes}",
        scene_index=scene_index,
    )


def flatten_timeline(scenes: list[Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    offset = 0.0
    for scene in scenes:
        for cue in scene.cues:
            events.append(
                {
                    "t": round(offset + cue.start_sec, 3),
                    "end": round(offset + cue.end_sec, 3),
                    "kind": cue.kind,
                    "display": display(cue.kind),
                    "scene": scene.scene_index,
                    "intensity": cue.intensity,
                    "particles": len(cue.particles),
                    "soft_body": cue.soft_body.kind if cue.soft_body else None,
                }
            )
        offset += float(scene.duration_seconds or 0)
    events.sort(key=lambda e: (e["t"], e["kind"]))
    return events

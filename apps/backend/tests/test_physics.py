"""Phase 3 Sprint 7 — Physics Engine tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PH = ROOT / "app" / "services" / "physics"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_pkg(pkg_name: str, pkg_path: Path, modules: list[tuple[str, str]]):
    pkg = type(sys)(pkg_name)
    pkg.__path__ = [str(pkg_path)]
    sys.modules[pkg_name] = pkg
    for mod_name, file_name in modules:
        _load(f"{pkg_name}.{mod_name}", pkg_path / file_name)
    _load(pkg_name, pkg_path / "__init__.py")


_load_pkg(
    "app.services.physics",
    PH,
    [
        ("models", "models.py"),
        ("catalog", "catalog.py"),
        ("detector", "detector.py"),
        ("forces", "forces.py"),
        ("soft_body", "soft_body.py"),
        ("effects", "effects.py"),
        ("bridge", "bridge.py"),
        ("store", "store.py"),
        ("engine", "engine.py"),
    ],
)

engine = sys.modules["app.services.physics.engine"]
catalog = sys.modules["app.services.physics.catalog"]
detector = sys.modules["app.services.physics.detector"]
forces = sys.modules["app.services.physics.forces"]


def test_catalog_mission_effects():
    required = {
        "hair_motion",
        "cloth_motion",
        "rain",
        "smoke",
        "dust",
        "wind",
        "explosion",
        "water",
        "fire",
        "particles",
        "gravity",
    }
    assert required.issubset(set(catalog.EFFECT_KINDS))


def test_detector_matrix():
    scores = detector.score_effects("Heavy rain and wind in the alley")
    assert scores["rain"] >= 0.9
    assert scores["wind"] >= 0.8

    ranked = detector.detect_effects(
        "Explosion tears through the warehouse with fire and smoke",
        always_soft_body=False,
    )
    kinds = {k for k, _ in ranked}
    assert "explosion" in kinds
    assert "fire" in kinds
    assert "smoke" in kinds


def test_forces():
    g = forces.build_gravity()
    assert g.vector[1] < 0
    w = forces.build_wind("gust from the left", intensity=0.8, storm=True)
    assert w.strength > 0.5
    assert w.turbulence > 0


def test_rain_and_soft_body_plan():
    plan = engine.build_physics_plan(
        "A woman walks through rain and wind; her hair and coat move naturally.",
        scenes=[
            {
                "index": 0,
                "title": "Rain Walk",
                "description": "walking in rain and wind",
                "environment": "city street night rain",
                "duration_seconds": 6,
                "actions": ["walk"],
                "characters": ["Hero_A"],
            }
        ],
        character_memory=[{"character_id": "Hero_A", "hair": "long"}],
        prompt_understanding={"weather": "rain", "emotion": "lonely"},
        motion_intelligence={
            "job_id": "motion_x",
            "primary_locomotion": ["walking"],
            "scenes": [{"scene_index": 0, "primary_locomotion": "walking"}],
        },
        director_plan={"cinematic_rhythm": "rising intensity"},
        parent_generation_id="gen_phys_1",
    )
    effects = set(plan.scenes[0].active_effects)
    assert "rain" in effects
    assert "wind" in effects
    assert "hair_motion" in effects
    assert "cloth_motion" in effects
    assert "gravity" in effects
    assert plan.scenes[0].cues
    assert any(c.particles for c in plan.scenes[0].cues)
    assert any(c.soft_body and c.soft_body.kind == "hair" for c in plan.scenes[0].cues)
    assert plan.global_gravity.strength > 0
    assert plan.particle_summary["systems"] >= 1
    assert plan.timeline
    assert engine.get_plan(plan.job_id) is not None


def test_explosion_fire_water_dust_smoke():
    plan = engine.build_physics_plan(
        "Massive explosion with fire, smoke, and dust; nearby water splashes.",
        duration_seconds=5,
        character_memory=[],
    )
    effects = set(plan.summary()["effects"])
    assert "explosion" in effects
    assert "fire" in effects or "smoke" in effects
    assert "gravity" in effects
    # Water from splash keyword
    assert "water" in effects or "dust" in effects


def test_each_effect_builds_cue():
    prompts = {
        "hair_motion": "Close-up of long hair blowing",
        "cloth_motion": "Silk dress fabric flowing",
        "rain": "Torrential rainfall on rooftops",
        "smoke": "Thick smoke fills the corridor",
        "dust": "Dust particles in sunbeam",
        "wind": "Strong wind across the desert",
        "explosion": "Building explosion at dusk",
        "water": "Ocean waves splash on rocks",
        "fire": "Campfire flames and embers",
        "particles": "Golden sparks and particles float",
        "gravity": "Objects falling under gravity",
    }
    for kind, prompt in prompts.items():
        plan = engine.build_physics_plan(prompt, duration_seconds=3)
        active = plan.scenes[0].active_effects
        assert kind in active, f"{kind} missing from {active} for {prompt!r}"
        cue = next(c for c in plan.scenes[0].cues if c.kind == kind)
        assert cue.intensity > 0
        assert cue.end_sec > cue.start_sec


def test_dict_export():
    result = engine.build_physics_dict("Windy night with dust", duration_seconds=4)
    assert "plan" in result and "summary" in result
    assert result["summary"]["job_id"].startswith("physics_")


if __name__ == "__main__":
    test_catalog_mission_effects()
    test_detector_matrix()
    test_forces()
    test_rain_and_soft_body_plan()
    test_explosion_fire_water_dust_smoke()
    test_each_effect_builds_cue()
    test_dict_export()
    print("OK physics")

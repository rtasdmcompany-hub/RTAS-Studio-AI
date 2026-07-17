"""Phase 3 Sprint 8 — Scene Render Engine tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SR = ROOT / "app" / "services" / "scene_render"


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
    # Do not exec __init__.py here — rebinding the package module can deadlock
    # under importlib file loaders when __init__ re-imports submodules.


_load_pkg(
    "app.services.scene_render",
    SR,
    [
        ("models", "models.py"),
        ("lighting", "lighting.py"),
        ("shadows", "shadows.py"),
        ("reflections", "reflections.py"),
        ("hdr", "hdr.py"),
        ("ray_tracing", "ray_tracing.py"),
        ("cache", "cache.py"),
        ("memory", "memory.py"),
        ("gpu_queue", "gpu_queue.py"),
        ("bridge", "bridge.py"),
        ("store", "store.py"),
        ("engine", "engine.py"),
    ],
)

# _load_pkg ends by exec __init__.py; if that hangs in some envs, submodules are enough.
engine = sys.modules["app.services.scene_render.engine"]
lighting = sys.modules["app.services.scene_render.lighting"]
hdr = sys.modules["app.services.scene_render.hdr"]
rt = sys.modules["app.services.scene_render.ray_tracing"]
gpu = sys.modules["app.services.scene_render.gpu_queue"]
cache = sys.modules["app.services.scene_render.cache"]
memory_mod = sys.modules["app.services.scene_render.memory"]


def setup_module():
    cache.clear_cache()
    gpu.clear_queue()


def test_lighting_and_hdr_night():
    setup_module()
    light = lighting.build_lighting("night rain city neon streets")
    assert light.volumetric is True
    assert light.color_temperature_k < 5000
    h = hdr.build_hdr("night neon bloom", quality="production", lighting_temp_k=light.color_temperature_k)
    assert h.enabled is True
    assert h.exposure < 0
    assert h.bloom > 0.2


def test_ray_tracing_ready_production():
    cfg = rt.build_ray_tracing("glass reflections", quality="production")
    assert cfg.ready is True
    assert cfg.samples_per_pixel >= 16
    assert cfg.denoise is True


def test_full_scene_render_plan():
    setup_module()
    plan = engine.build_scene_render_plan(
        "Cinematic night rain with wet street reflections and neon.",
        scenes=[
            {
                "index": 0,
                "title": "Alley",
                "description": "wet street reflections neon rain",
                "environment": "night city rain",
                "duration_seconds": 5,
            },
            {
                "index": 1,
                "title": "Close",
                "description": "soft portrait under practical lamp",
                "environment": "interior",
                "duration_seconds": 4,
            },
        ],
        director_plan={"cinematic_rhythm": "rising intensity"},
        production_render={"validation": {"passed": True}},
        prompt_understanding={"weather": "rain", "lighting": "neon practicals"},
        visual_style={"lighting": "practical-motivated", "look": "filmic"},
        physics={
            "job_id": "physics_x",
            "effects": ["rain", "wind", "gravity"],
            "scenes": [
                {"scene_index": 0, "active_effects": ["rain", "wind", "gravity"]},
                {"scene_index": 1, "active_effects": ["gravity"]},
            ],
        },
        camera_motion={
            "job_id": "cam_x",
            "primary_motions": ["tracking", "push_in"],
        },
        quality="production",
        enqueue_gpu=True,
        parent_generation_id="gen_sr_1",
    )

    assert plan.job_id.startswith("scenerender_")
    assert len(plan.scenes) == 2
    assert plan.hdr_enabled is True
    assert plan.ray_tracing_ready is True
    assert plan.quality == "production"
    s0 = plan.scenes[0]
    assert s0.lighting.volumetric is True
    assert s0.shadows.enabled is True
    assert s0.reflections.enabled is True
    assert s0.hdr.enabled is True
    assert s0.ray_tracing.ready is True
    assert s0.cache.cache_key
    assert s0.memory.target_vram_mb >= 4096
    assert s0.gpu_job.state == "queued"
    assert len(plan.gpu_queue) == 2
    assert plan.scene_cache
    assert plan.memory_optimization.get("streaming") is True
    assert plan.timeline
    assert plan.director_integration.get("parent_generation_id") == "gen_sr_1"
    assert plan.physics_integration.get("physics_job_id") == "physics_x"

    # GPU dequeue + complete
    job = gpu.dequeue()
    assert job is not None
    assert job.state == "running"
    done = gpu.complete(job.job_id)
    assert done and done.state == "completed"

    summary = plan.summary()
    assert summary["scenes"] == 2
    assert summary["gpu_jobs"] == 2
    assert engine.get_plan(plan.job_id) is not None


def test_cache_hit_increments():
    setup_module()
    scene = {"index": 0, "title": "A", "description": "daylight plaza", "environment": "exterior"}
    a = cache.build_cache_entry(
        scene, scene_index=0, lighting_key="soft key", quality="preview", duration_seconds=3
    )
    b = cache.build_cache_entry(
        scene, scene_index=0, lighting_key="soft key", quality="preview", duration_seconds=3
    )
    assert a.cache_key == b.cache_key
    assert b.hits >= 1


def test_memory_budgets_scale():
    draft = memory_mod.build_memory_budget(quality="draft", scene_count=1)
    cinema = memory_mod.build_memory_budget(
        quality="cinema",
        scene_count=4,
        particle_heavy=True,
        physics_effects=["explosion", "fire"],
    )
    assert cinema.target_vram_mb > draft.target_vram_mb
    assert cinema.particle_budget_mb > draft.particle_budget_mb
    opt = memory_mod.optimize_memory_plan([draft, cinema], quality="cinema")
    assert opt["target_vram_mb"] == cinema.target_vram_mb


def test_dict_export():
    setup_module()
    result = engine.build_scene_render_dict(
        "Bright desert noon hard sun",
        quality="preview",
        duration_seconds=3,
        enqueue_gpu=False,
    )
    assert "plan" in result and "summary" in result
    assert result["plan"]["hdr_enabled"] is True
    assert result["summary"]["job_id"].startswith("scenerender_")


if __name__ == "__main__":
    test_lighting_and_hdr_night()
    test_ray_tracing_ready_production()
    test_full_scene_render_plan()
    test_cache_hit_increments()
    test_memory_budgets_scale()
    test_dict_export()
    print("OK scene_render")

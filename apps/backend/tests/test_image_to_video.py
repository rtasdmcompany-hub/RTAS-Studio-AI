"""Phase 3 Sprint 2 — Image-to-Video Engine tests."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
I2V = ROOT / "app" / "services" / "image_to_video"

PACKAGE = {
    "prompt": "Product hero shot on wet asphalt at night",
    "enhanced_prompt": "Cinematic product reveal, rain reflections",
    "director_plan": {"director_notes": ["Keep logo sharp", "Preserve lighting"]},
    "scene_breakdown": {
        "Production": {
            "Scenes": [
                {
                    "scene_number": 1,
                    "title": "Hero Establish",
                    "scene_purpose": "Show product in world",
                    "estimated_duration_seconds": 4,
                    "environment": "Wet street",
                    "weather": "Rain",
                    "time": "Night",
                },
                {
                    "scene_number": 2,
                    "title": "Detail Push",
                    "scene_purpose": "Detail logo",
                    "estimated_duration_seconds": 3,
                    "environment": "Wet street",
                    "weather": "Rain",
                    "time": "Night",
                },
            ],
            "Shots": [
                {
                    "scene_number": 1,
                    "shot_number": 1,
                    "shot_type": "Wide Shot",
                    "camera_movement": "Push In",
                    "purpose": "Establish",
                    "estimated_duration_seconds": 4,
                },
                {
                    "scene_number": 2,
                    "shot_number": 1,
                    "shot_type": "Close Up",
                    "camera_movement": "Slider",
                    "purpose": "Logo detail",
                    "estimated_duration_seconds": 3,
                },
            ],
        }
    },
}


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
    "app.services.image_to_video",
    I2V,
    [
        ("models", "models.py"),
        ("validation", "validation.py"),
        ("metadata", "metadata.py"),
        ("prompts", "prompts.py"),
        ("scene_map", "scene_map.py"),
        ("provider_map", "provider_map.py"),
        ("queue", "queue.py"),
        ("store", "store.py"),
        ("retry", "retry.py"),
        ("engine", "engine.py"),
    ],
)

engine = sys.modules["app.services.image_to_video.engine"]
queue_mod = sys.modules["app.services.image_to_video.queue"]
store_mod = sys.modules["app.services.image_to_video.store"]
validation = sys.modules["app.services.image_to_video.validation"]
metadata = sys.modules["app.services.image_to_video.metadata"]
retry_mod = sys.modules["app.services.image_to_video.retry"]
models = sys.modules["app.services.image_to_video.models"]


def _reset():
    queue_mod.i2v_queue.clear()
    store_mod.clear_all_stores()


def test_image_validation_and_roles():
    _reset()
    assets = metadata.ingest_image_inputs(
        single_image="https://cdn.example.com/hero.jpg",
        character_reference="https://cdn.example.com/face.png",
        product_reference="https://cdn.example.com/product.webp",
        logo_reference="https://cdn.example.com/logo.png",
        multiple_images=[
            "https://cdn.example.com/f1.jpg",
            "https://cdn.example.com/f2.jpg",
        ],
        reference_images=["https://cdn.example.com/style.jpg"],
    )
    roles = {a.role for a in assets}
    assert roles >= {"single", "character", "product", "logo", "multiple", "reference"}
    result = validation.validate_images(assets, require_character_for_identity=True)
    assert result.passed is True
    assert result.checks["has_images"]
    assert result.checks["has_character_ref"]


def test_prompt_merge_preserves_locks():
    _reset()
    job = engine.build_image_to_video_job(
        prompt="Slow orbit around the bottle",
        character_reference="https://cdn.example.com/face.jpg",
        product_reference="https://cdn.example.com/bottle.jpg",
        logo_reference="https://cdn.example.com/logo.png",
        production_package=PACKAGE,
        scene_breakdown=PACKAGE["scene_breakdown"],
        director_plan=PACKAGE["director_plan"],
        preserve_identity=True,
        preserve_lighting=True,
        preserve_composition=True,
        preserve_environment=True,
    )
    assert job.validation.passed
    assert job.requests
    prompt = job.requests[0].prompt
    assert "Preserve:" in prompt
    assert "identity" in prompt.lower()
    assert "lighting" in prompt.lower()
    assert "composition" in prompt.lower()
    assert "environment" in prompt.lower()
    assert job.requests[0].primary_image_url
    payload = job.requests[0].to_provider_payload()
    assert payload["mode"] == "image"
    assert payload["arguments"]["image_url"]
    print("i2v_provider_payload=")
    print(json.dumps(payload, indent=2)[:700])


def test_scene_mapping_and_queue():
    _reset()
    job = engine.build_and_register(
        prompt="Animate product in rain",
        single_image="https://cdn.example.com/hero.jpg",
        product_reference="https://cdn.example.com/product.jpg",
        production_package=PACKAGE,
        scene_breakdown=PACKAGE["scene_breakdown"],
        enqueue=True,
    )
    assert job.state == "queued"
    assert len(job.scene_bindings) == 2
    assert len(job.requests) == 2
    assert queue_mod.i2v_queue.size() == 2
    stored = store_mod.metadata_store.get_job(job.job_id)
    assert stored and stored.image_metadata
    hist = store_mod.history_store.for_job(job.job_id)
    assert any(h.event == "validation" for h in hist)
    assert any(h.event == "requests_queued" for h in hist)


def test_retry_then_success():
    _reset()
    job = engine.build_and_register(
        prompt="Move camera subtly",
        character_reference="https://cdn.example.com/face.jpg",
        enqueue=True,
    )
    calls = {"n": 0}

    async def flaky(req):
        calls["n"] += 1
        if req.attempts == 0 and calls["n"] == 1:
            return {"success": False, "error": "temporary timeout"}
        return {
            "success": True,
            "remote_url": f"https://example.com/{req.request_id}.mp4",
            "external_job_id": f"ext-{req.request_id}",
            "provider": "simulation",
        }

    done = asyncio.run(
        engine.process_job_queue(
            job.job_id,
            generate_fn=flaky,
            policy=models.RetryPolicy(max_attempts=3, base_delay_seconds=0.0),
            sleep_on_retry=False,
        )
    )
    assert done and done.state == "completed"
    history = engine.get_job_history(job.job_id)
    events = {h["event"] for h in history}
    assert "request_failed" in events
    assert "request_requeued" in events
    assert "job_completed" in events


def test_validation_fails_without_images():
    _reset()
    job = engine.build_and_register(prompt="no images here", enqueue=True)
    assert job.validation.passed is False
    assert job.state == "failed"
    assert queue_mod.i2v_queue.size() == 0


if __name__ == "__main__":
    test_image_validation_and_roles()
    test_prompt_merge_preserves_locks()
    test_scene_mapping_and_queue()
    test_retry_then_success()
    test_validation_fails_without_images()
    print("image_to_video tests: ok")

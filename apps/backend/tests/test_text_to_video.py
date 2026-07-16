"""Phase 3 Sprint 1 — Real Text-to-Video Engine tests."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ROOT / "app" / "services"
T2V = SERVICES / "text_to_video"

EXAMPLE_PACKAGE = {
    "prompt": "A lonely Pakistani man walks through the rain at night.",
    "enhanced_prompt": "Cinematic rain night walk, emotional, photoreal.",
    "character_memory": [
        {
            "character_id": "Character_A",
            "gender": "male",
            "age": "30s",
            "hair": "dark",
            "outfit": "dark coat",
            "face_shape": "oval",
            "eye_color": "brown",
            "reference_image_urls": ["https://example.com/face.jpg"],
        }
    ],
    "director_plan": {
        "director_notes": ["Protect face identity", "Rain continuity"],
        "transition_style": "motivated cut",
    },
    "scene_breakdown": {
        "Production": {
            "prompt": "A lonely Pakistani man walks through the rain at night.",
            "Scenes": [
                {
                    "scene_number": 1,
                    "title": "Opening Establishing Shot",
                    "scene_purpose": "Establish world",
                    "estimated_duration_seconds": 4,
                    "environment": "Empty road",
                    "weather": "Rain",
                    "time": "Night",
                    "character_emotion": "Lonely",
                },
                {
                    "scene_number": 2,
                    "title": "Walking Shot",
                    "scene_purpose": "Follow subject",
                    "estimated_duration_seconds": 5,
                    "environment": "Empty road",
                    "weather": "Rain",
                    "time": "Night",
                    "character_emotion": "Lonely",
                },
            ],
            "Shots": [
                {
                    "scene_number": 1,
                    "shot_number": 1,
                    "shot_type": "Extreme Wide",
                    "camera_angle": "High Angle",
                    "lens": "24mm wide",
                    "camera_movement": "Reveal",
                    "lighting": ["Low Key", "Blue"],
                    "environment": "Empty road",
                    "weather": "Rain",
                    "time": "Night",
                    "character_emotion": "Lonely",
                    "facial_expression": "distant gaze",
                    "body_language": "closed posture",
                    "color_palette": ["Cold Blue"],
                    "depth_of_field": "deep focus",
                    "composition": "leading lines",
                    "transition_type": "cut",
                    "purpose": "Establish world",
                    "estimated_duration_seconds": 4,
                },
                {
                    "scene_number": 2,
                    "shot_number": 1,
                    "shot_type": "Tracking",
                    "camera_angle": "Eye Level",
                    "lens": "35mm narrative",
                    "camera_movement": "Tracking",
                    "lighting": ["Low Key"],
                    "environment": "Empty road",
                    "weather": "Rain",
                    "time": "Night",
                    "character_emotion": "Lonely",
                    "purpose": "Follow walk",
                    "estimated_duration_seconds": 5,
                    "transition_type": "soft dissolve",
                },
            ],
            "EstimatedRuntime": 9,
        }
    },
    "production_render": {
        "export_specs": [
            {
                "format": "mp4",
                "aspect": "landscape",
                "resolution": "1080p",
                "hdr": True,
            }
        ]
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
    "app.services.text_to_video",
    T2V,
    [
        ("models", "models.py"),
        ("prompts", "prompts.py"),
        ("mapper", "mapper.py"),
        ("queue", "queue.py"),
        ("store", "store.py"),
        ("retry", "retry.py"),
        ("engine", "engine.py"),
    ],
)

engine = sys.modules["app.services.text_to_video.engine"]
queue_mod = sys.modules["app.services.text_to_video.queue"]
store_mod = sys.modules["app.services.text_to_video.store"]
retry_mod = sys.modules["app.services.text_to_video.retry"]
mapper = sys.modules["app.services.text_to_video.mapper"]


def _reset():
    queue_mod.t2v_queue.clear()
    store_mod.clear_all_stores()


def test_map_production_package_to_provider_requests():
    _reset()
    job = mapper.map_production_package_to_job(
        EXAMPLE_PACKAGE,
        character_memory=EXAMPLE_PACKAGE["character_memory"],
        director_plan=EXAMPLE_PACKAGE["director_plan"],
        production_render=EXAMPLE_PACKAGE["production_render"],
        parent_generation_id="gen_test_1",
    )
    assert job.job_id.startswith("t2v_")
    assert len(job.scenes) == 2
    assert len(job.shots) == 2
    assert len(job.requests) == 2
    req = job.requests[0]
    assert req.scene_number == 1
    assert req.shot_number == 1
    assert "Extreme Wide" in req.prompt or "IDENTITY LOCK" in req.prompt
    assert req.duration_seconds >= 2
    assert req.aspect == "landscape"
    assert req.hdr is True
    payload = req.to_provider_payload()
    assert payload["compiled_prompt"]
    assert payload["arguments"]["prompt"]
    print("provider_request_example=")
    print(json.dumps(payload, indent=2)[:800])


def test_queue_and_metadata_storage():
    _reset()
    job = engine.build_and_register_from_intelligence(
        production_package=EXAMPLE_PACKAGE,
        character_memory=EXAMPLE_PACKAGE["character_memory"],
        director_plan=EXAMPLE_PACKAGE["director_plan"],
        scene_breakdown=EXAMPLE_PACKAGE["scene_breakdown"],
        production_render=EXAMPLE_PACKAGE["production_render"],
        parent_generation_id="gen_q1",
        enqueue=True,
    )
    assert job.state == "queued"
    assert queue_mod.t2v_queue.size() == 2
    stored = store_mod.metadata_store.get_job(job.job_id)
    assert stored is not None
    assert stored.scenes[0].scene_id
    assert stored.shots[0].shot_id
    scene = store_mod.metadata_store.get_scene(stored.scenes[0].scene_id)
    shot = store_mod.metadata_store.get_shot(stored.shots[0].shot_id)
    assert scene and shot
    hist = store_mod.history_store.for_job(job.job_id)
    assert any(h.event == "job_created" for h in hist)
    assert any(h.event == "requests_queued" for h in hist)


def test_retry_policy():
    _reset()
    from app.services.text_to_video.models import ProviderGenerationRequest, RetryPolicy

    req = ProviderGenerationRequest(
        request_id="r1",
        job_id="j1",
        scene_id="s1",
        shot_id="sh1",
        scene_number=1,
        shot_number=1,
        prompt="test",
        duration_seconds=3,
        max_attempts=3,
    )
    policy = RetryPolicy(max_attempts=3, base_delay_seconds=0.01)
    assert retry_mod.is_retryable_error("timeout from provider", policy)
    assert not retry_mod.is_retryable_error("moderation blocked", policy)
    assert retry_mod.mark_for_retry(req, error="rate limit exceeded", policy=policy)
    assert req.state == "retrying"
    assert req.attempts == 1
    assert retry_mod.mark_for_retry(req, error="503 unavailable", policy=policy)
    assert req.attempts == 2
    # third failure exhausts
    assert not retry_mod.mark_for_retry(req, error="timeout", policy=policy)
    assert req.state == "failed"
    assert req.attempts == 3


def test_process_queue_with_retry_then_success():
    _reset()
    job = engine.build_and_register_from_intelligence(
        production_package=EXAMPLE_PACKAGE,
        scene_breakdown=EXAMPLE_PACKAGE["scene_breakdown"],
        character_memory=EXAMPLE_PACKAGE["character_memory"],
        enqueue=True,
    )
    calls = {"n": 0}

    async def flaky(req):
        calls["n"] += 1
        # Fail first request once with retryable error, then succeed
        if req.shot_number == 1 and req.attempts == 0 and calls["n"] == 1:
            return {"success": False, "error": "temporary timeout"}
        return {
            "success": True,
            "remote_url": f"https://example.com/{req.request_id}.mp4",
            "external_job_id": f"ext-{req.request_id}",
            "provider": "simulation",
        }

    from app.services.text_to_video.models import RetryPolicy

    done = asyncio.run(
        engine.process_job_queue(
            job.job_id,
            generate_fn=flaky,
            policy=RetryPolicy(max_attempts=3, base_delay_seconds=0.0),
            sleep_on_retry=False,
        )
    )
    assert done is not None
    assert done.state == "completed"
    assert all(r.state == "completed" for r in done.requests)
    assert any(r.attempts >= 2 for r in done.requests)  # retried shot
    history = engine.get_job_history(job.job_id)
    events = {h["event"] for h in history}
    assert "request_failed" in events
    assert "request_requeued" in events
    assert "request_completed" in events
    assert "job_completed" in events
    print("history_events=", sorted(events))


def test_integration_scene_by_scene_requests():
    _reset()
    result = engine.build_text_to_video_dict(
        EXAMPLE_PACKAGE,
        scene_breakdown=EXAMPLE_PACKAGE["scene_breakdown"],
        character_memory=EXAMPLE_PACKAGE["character_memory"],
        director_plan=EXAMPLE_PACKAGE["director_plan"],
        production_render=EXAMPLE_PACKAGE["production_render"],
        enqueue=True,
    )
    assert result["summary"]["scenes"] == 2
    assert result["summary"]["shots"] == 2
    assert result["summary"]["requests"] == 2
    assert len(result["provider_payloads"]) == 2
    assert result["provider_payloads"][0]["scene_number"] == 1
    assert result["provider_payloads"][1]["scene_number"] == 2
    # Process simulate
    job_id = result["job"]["job_id"]
    finished = asyncio.run(engine.process_job_queue(job_id))
    assert finished and finished.state == "completed"


if __name__ == "__main__":
    test_map_production_package_to_provider_requests()
    test_queue_and_metadata_storage()
    test_retry_policy()
    test_process_queue_with_retry_then_success()
    test_integration_scene_by_scene_requests()
    print("text_to_video tests: ok")

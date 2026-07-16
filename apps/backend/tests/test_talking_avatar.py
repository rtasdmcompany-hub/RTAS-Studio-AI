"""Phase 3 Sprint 3 — Talking Avatar Engine tests."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AV = ROOT / "app" / "services" / "talking_avatar"


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
    "app.services.talking_avatar",
    AV,
    [
        ("models", "models.py"),
        ("face_lock", "face_lock.py"),
        ("lip_sync", "lip_sync.py"),
        ("emotion", "emotion.py"),
        ("motion", "motion.py"),
        ("timeline", "timeline.py"),
        ("prompts", "prompts.py"),
        ("store", "store.py"),
        ("engine", "engine.py"),
    ],
)

engine = sys.modules["app.services.talking_avatar.engine"]
store = sys.modules["app.services.talking_avatar.store"]


AUDIO = {
    "detection": {"emotion": "confident", "language": "en"},
    "voice_timeline": [{"start_sec": 0.2, "end_sec": 6.0, "label": "VO"}],
    "lip_sync_timeline": [
        {
            "start_sec": 0.2,
            "end_sec": 0.5,
            "character_id": "Avatar_A",
            "phoneme_hint": "HE",
            "mouth_openness": 0.6,
            "viseme": "AA",
            "dialogue_snippet": "Hello everyone",
            "sync_confidence": 0.9,
        },
        {
            "start_sec": 0.5,
            "end_sec": 0.9,
            "character_id": "Avatar_A",
            "phoneme_hint": "LO",
            "mouth_openness": 0.55,
            "viseme": "OU",
            "dialogue_snippet": "Hello everyone",
            "sync_confidence": 0.88,
        },
    ],
    "estimated_runtime_seconds": 10,
}

CHARS = [
    {
        "character_id": "Avatar_A",
        "gender": "female",
        "hair": "dark wavy",
        "eye_color": "brown",
        "outfit": "blazer",
        "reference_image_urls": ["https://cdn.example.com/face.jpg"],
        "locked_traits": ["face", "hair", "outfit"],
    }
]

DIRECTOR = {
    "director_notes": ["Hold eye contact on key lines", "Soft smile on greeting"],
    "cinematic_rhythm": "presenter clarity",
    "transition_style": "clean cuts",
    "emotional_pacing": ["confident"],
}


def _reset():
    store.clear_all()


def test_face_lock_and_character_memory():
    _reset()
    job = engine.build_talking_avatar_job(
        prompt="Talking avatar host welcomes viewers",
        character_memory=CHARS,
        reference_face_url="https://cdn.example.com/face.jpg",
        director_plan=DIRECTOR,
        audio_director=AUDIO,
        natural_motion=True,
    )
    assert job.face_lock.face_locked is True
    assert job.face_lock.character_id == "Avatar_A"
    assert job.face_lock.reference_face_url.endswith("face.jpg")
    assert "face" in job.face_lock.locked_traits


def test_timeline_has_all_motion_channels():
    _reset()
    job = engine.build_and_register(
        prompt="Professional talking avatar presenter",
        character_memory=CHARS,
        director_plan=DIRECTOR,
        audio_director=AUDIO,
        duration_hint=10,
        natural_motion=True,
    )
    tl = job.timeline
    assert tl.runtime_seconds >= 10
    assert tl.lip_sync  # face animation / lip sync
    assert tl.head_motion
    assert tl.eye_contact
    assert tl.blinks
    assert tl.expressions
    assert tl.idle_motion
    assert job.emotion in ("confident", "neutral", "professional")
    assert job.natural_motion is True
    # smiles for confident/happy-ish
    assert isinstance(tl.smiles, list)
    payload = job.provider_request.to_provider_payload()
    assert payload["mode"] == "avatar"
    assert payload["arguments"]["talking_head"] is True
    assert payload["arguments"]["lip_sync"] is True
    assert "REFERENCE FACE LOCK" in payload["compiled_prompt"]
    print("avatar_timeline_summary=")
    print(
        json.dumps(
            {
                "lip_sync": len(tl.lip_sync),
                "head": len(tl.head_motion),
                "eyes": len(tl.eye_contact),
                "blinks": len(tl.blinks),
                "smiles": len(tl.smiles),
                "idle": len(tl.idle_motion),
                "emotion": job.emotion,
            },
            indent=2,
        )
    )


def test_dialogue_fallback_lip_sync():
    _reset()
    job = engine.build_talking_avatar_job(
        prompt="Avatar says hello",
        dialogue="Hello friends, welcome to RTAS Studio.",
        character_memory=CHARS,
        duration_hint=6,
        audio_director=None,
    )
    assert job.timeline.lip_sync
    assert any(f.viseme for f in job.timeline.lip_sync)


def test_history_and_store():
    _reset()
    result = engine.build_talking_avatar_dict(
        prompt="Digital human presenter",
        character_memory=CHARS,
        director_plan=DIRECTOR,
        audio_director=AUDIO,
        reference_face_url="https://cdn.example.com/face.jpg",
    )
    assert result["summary"]["face_locked"] is True
    assert result["summary"]["lip_sync_cues"] >= 1
    assert result["providerPayload"]["face_reference_url"]
    hist = result["history"]
    assert any(h["event"] == "job_created" for h in hist)
    assert any(h["event"] == "face_lock" for h in hist)
    assert any(h["event"] == "timeline_ready" for h in hist)
    stored = engine.get_job(result["job"]["job_id"])
    assert stored is not None


if __name__ == "__main__":
    test_face_lock_and_character_memory()
    test_timeline_has_all_motion_channels()
    test_dialogue_fallback_lip_sync()
    test_history_and_store()
    print("talking_avatar tests: ok")

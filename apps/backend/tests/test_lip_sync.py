"""Phase 3 Sprint 4 — Professional Lip Sync Engine tests."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LS = ROOT / "app" / "services" / "lip_sync"


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
    "app.services.lip_sync",
    LS,
    [
        ("models", "models.py"),
        ("languages", "languages.py"),
        ("phonemes", "phonemes.py"),
        ("visemes", "visemes.py"),
        ("alignment", "alignment.py"),
        ("emotion_sync", "emotion_sync.py"),
        ("engine", "engine.py"),
    ],
)

engine = sys.modules["app.services.lip_sync.engine"]
languages = sys.modules["app.services.lip_sync.languages"]


def test_language_detection_matrix():
    assert languages.detect_language("Hello friends welcome") == "en"
    assert languages.detect_language("Urdu dialogue in Pakistan night rain") == "ur"
    assert languages.detect_language("Arabic nasheed about faith") == "ar"
    assert languages.detect_language("Hindi bollywood emotional scene") == "hi"
    assert languages.detect_language("Punjabi folk song celebration") == "pa"
    # Arabic script → ur by default (RTAS), ar when arabic keywords
    assert languages.detect_language("مرحبا بكم") in ("ur", "ar")
    assert languages.detect_language("Arabic: مرحبا") == "ar"


def test_phoneme_viseme_alignment_emotion():
    plan = engine.build_lip_sync_plan(
        "Hello everyone, welcome to RTAS Studio.",
        language_hint="en",
        emotion_hint="confident",
        duration_seconds=6.0,
        character_id="Avatar_A",
    )
    assert plan.language == "en"
    assert plan.phonemes
    assert plan.visemes
    assert plan.alignment.duration_seconds > 0
    assert plan.alignment.words
    assert plan.timeline
    assert plan.emotion == "confident"
    assert all(v.viseme for v in plan.visemes)
    assert all(0.0 <= v.mouth_openness <= 1.0 for v in plan.visemes)
    # Emotion sync applied
    assert all(v.emotion == "confident" for v in plan.visemes)
    cues = plan.to_audio_director_cues()
    assert cues and "viseme" in cues[0]
    print("en_plan_summary=")
    print(json.dumps(plan.summary(), indent=2))


def test_urdu_arabic_hindi_punjabi_plans():
    cases = [
        ("ur", "Pakistani urdu emotional monologue in the rain"),
        ("ar", "Arabic nasheed spiritual greeting"),
        ("hi", "Hindi bollywood romantic dialogue"),
        ("pa", "Punjabi celebration folk greeting"),
    ]
    for lang, text in cases:
        plan = engine.build_lip_sync_plan(
            text,
            language_hint=lang,
            emotion_hint="happy",
            duration_seconds=5.0,
        )
        assert plan.language == lang, f"{text} -> {plan.language}"
        assert plan.visemes
        assert plan.alignment.speech_end_sec > plan.alignment.speech_start_sec
        assert lang in plan.languages_detected or plan.language == lang


def test_speech_alignment_with_voice_timeline():
    plan = engine.build_lip_sync_plan(
        "Look at me now",
        language_hint="en",
        voice_timeline=[
            {"start_sec": 1.0, "end_sec": 3.5, "kind": "dialogue"},
        ],
    )
    assert plan.alignment.speech_start_sec == 1.0
    assert plan.alignment.speech_end_sec == 3.5
    assert plan.visemes[0].start_sec >= 1.0
    assert plan.visemes[-1].end_sec <= 3.5 + 0.01


def test_dict_api():
    result = engine.build_lip_sync_dict(
        "Hello friends",
        language_hint="en",
        emotion_hint="joy",
        duration_seconds=4,
    )
    assert result["summary"]["visemes"] >= 1
    assert result["timeline"]
    assert result["audioDirectorCues"]


if __name__ == "__main__":
    test_language_detection_matrix()
    test_phoneme_viseme_alignment_emotion()
    test_urdu_arabic_hindi_punjabi_plans()
    test_speech_alignment_with_voice_timeline()
    test_dict_api()
    print("lip_sync tests: ok")

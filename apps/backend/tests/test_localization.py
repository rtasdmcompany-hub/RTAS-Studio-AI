"""Phase 4 Sprint 7 — Multi-Language Dubbing & Localization tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOC = ROOT / "app" / "services" / "localization"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _ensure_parents(pkg_name: str):
    parts = pkg_name.split(".")
    for i in range(1, len(parts)):
        parent = ".".join(parts[:i])
        if parent not in sys.modules:
            mod = type(sys)(parent)
            mod.__path__ = []
            sys.modules[parent] = mod


def _load_pkg(pkg_name: str, pkg_path: Path, modules: list[tuple[str, str]]):
    _ensure_parents(pkg_name)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    pkg = type(sys)(pkg_name)
    pkg.__path__ = [str(pkg_path)]
    sys.modules[pkg_name] = pkg
    for mod_name, file_name in modules:
        _load(f"{pkg_name}.{mod_name}", pkg_path / file_name)


_load_pkg(
    "app.services.localization",
    LOC,
    [
        ("version", "version.py"),
        ("languages", "languages.py"),
        ("models", "models.py"),
        ("validation", "validation.py"),
        ("translation", "translation.py"),
        ("speakers", "speakers.py"),
        ("subtitles", "subtitles.py"),
        ("store", "store.py"),
        ("queue", "queue.py"),
        ("cache", "cache.py"),
        ("observability", "observability.py"),
        ("engine", "engine.py"),
    ],
)

version = sys.modules["app.services.localization.version"]
languages = sys.modules["app.services.localization.languages"]
validation = sys.modules["app.services.localization.validation"]
translation = sys.modules["app.services.localization.translation"]
store = sys.modules["app.services.localization.store"]
queue_mod = sys.modules["app.services.localization.queue"]
engine = sys.modules["app.services.localization.engine"]


def setup_function():
    store.clear()
    queue_mod.localization_queue.clear()
    translation.memory_clear()


def test_version():
    assert version.ENGINE_VERSION == "1.0.0"
    assert "Localization" in version.ENGINE_NAME
    assert version.SPRINT == 7


def test_languages_pluggable():
    codes = {l["code"] for l in languages.list_languages()}
    required = {"en", "ur", "hi", "ar", "pa", "tr", "es", "fr", "de", "zh", "ja", "ko"}
    assert required <= codes
    languages.register_language(
        languages.LanguageProfile("it", "Italian", "Italiano", default_locale="it-IT")
    )
    assert languages.is_supported("it")


def test_validation_and_translation():
    bad = validation.validate_localization_request(text="", target_language="zz")
    assert not bad.ok
    good = validation.validate_localization_request(
        text="Hello welcome", source_language="en", target_language="ur"
    )
    assert good.ok
    tr = translation.translate_text("Hello", source_language="en", target_language="ur")
    assert tr["translated_text"]
    assert not tr["from_memory"]
    tr2 = translation.translate_text("Hello", source_language="en", target_language="ur")
    assert tr2["from_memory"]


def test_translate_and_dub():
    setup_function()
    tjob = engine.translate(
        "Welcome to RTAS Studio AI. Thank you.",
        source_language="en",
        target_language="hi",
        duration_sec=8,
    )
    assert tjob.job_id.startswith("locjob_")
    assert tjob.kind == "translate"
    assert tjob.state == "completed"
    assert tjob.translated_text
    assert len(tjob.subtitles) >= 1

    djob = engine.dub(
        'Hello said the hero. "We must go now."',
        source_language="en",
        target_language="es",
        duration_sec=10,
        character_memory=[
            {
                "character_id": "Character_A",
                "gender": "male",
                "default_voice": "rtas_en_male_01",
                "clone_id": "voiceclone_x",
                "accent": "neutral",
            }
        ],
        voice_summary={"job_id": "voicejob_1", "voice_id": "rtas_en_male_01"},
    )
    assert djob.kind == "dub"
    assert djob.production_ready
    assert djob.voice_preserved
    assert len(djob.audio_tracks) >= 1
    assert djob.lip_sync_metadata.get("synced_to_timeline") is True
    assert djob.metadata["provider_secret_exposed"] is False
    assert djob.speakers[0].character_id == "Character_A"


def test_queue_retry_cancel():
    setup_function()
    job = engine.localize(
        "Test queue path.",
        source_language="en",
        target_language="fr",
        enqueue=True,
        auto_process=False,
    )
    assert job.state == "queued"
    processed = engine.process_localization_job(job.job_id)
    assert processed and processed.state == "completed"
    queue_mod.localization_queue.update_state(job.job_id, "failed", error="boom")
    retried = queue_mod.localization_queue.retry(job.job_id)
    assert retried and retried.state == "retrying"
    again = engine.process_localization_job(job.job_id)
    assert again and again.state == "completed"

    job2 = engine.translate(
        "Cancel me",
        target_language="de",
        enqueue=True,
        auto_process=False,
    )
    cancelled = queue_mod.localization_queue.cancel(job2.job_id)
    assert cancelled and cancelled.state == "cancelled"


def test_performance():
    setup_function()
    t0 = time.perf_counter()
    for i in range(20):
        engine.dub(
            f"Scene dialogue number {i}. Welcome.",
            source_language="en",
            target_language="tr",
            duration_sec=5,
            auto_process=True,
        )
    elapsed = time.perf_counter() - t0
    assert elapsed < 5.0, f"20 dubs took {elapsed:.2f}s"


def run_all():
    tests = [
        test_version,
        test_languages_pluggable,
        test_validation_and_translation,
        test_translate_and_dub,
        test_queue_retry_cancel,
        test_performance,
    ]
    for fn in tests:
        setup_function()
        fn()
    print("OK localization")


if __name__ == "__main__":
    run_all()

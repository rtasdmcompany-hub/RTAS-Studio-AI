"""Phase 4 Sprint 2 — Voice Generation Engine tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VG = ROOT / "app" / "services" / "voice_generation"


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
    "app.services.voice_generation",
    VG,
    [
        ("version", "version.py"),
        ("languages", "languages.py"),
        ("presets", "presets.py"),
        ("models", "models.py"),
        ("ssml", "ssml.py"),
        ("quality", "quality.py"),
        ("validation", "validation.py"),
        ("store", "store.py"),
        ("queue", "queue.py"),
        ("observability", "observability.py"),
        ("export", "export.py"),
        ("engine", "engine.py"),
    ],
)

engine = sys.modules["app.services.voice_generation.engine"]
version = sys.modules["app.services.voice_generation.version"]
languages = sys.modules["app.services.voice_generation.languages"]
presets = sys.modules["app.services.voice_generation.presets"]
validation = sys.modules["app.services.voice_generation.validation"]
queue_mod = sys.modules["app.services.voice_generation.queue"]
ssml = sys.modules["app.services.voice_generation.ssml"]
quality = sys.modules["app.services.voice_generation.quality"]
models = sys.modules["app.services.voice_generation.models"]


def test_version():
    assert version.ENGINE_VERSION == "1.0.0"
    assert "Voice Generation" in version.ENGINE_NAME


def test_languages_pluggable():
    codes = {l["code"] for l in languages.list_languages()}
    assert {"en", "ur", "hi", "ar", "pa"} <= codes
    assert languages.normalize_language("ur-PK") == "ur"
    try:
        languages.normalize_language("zz")
        assert False, "expected ValueError"
    except ValueError:
        pass
    languages.register_language(
        languages.LanguageSpec("fr", "French", "Français", default_locale="fr-FR")
    )
    assert languages.normalize_language("fr") == "fr"


def test_voice_validation():
    bad = validation.validate_generate_request(
        text="",
        language="en",
        voice_id=None,
        gender="female",
        speed=1.0,
        pitch=0.0,
        volume=1.0,
        pause_ms=0,
    )
    assert bad.ok is False
    good = validation.validate_generate_request(
        text="Hello from RTAS Studio",
        language="hi",
        voice_id=None,
        gender="male",
        speed=1.0,
        pitch=0.0,
        volume=1.0,
        pause_ms=100,
    )
    assert good.ok is True
    assert good.voice_id.startswith("rtas_hi_male")


def test_ssml_and_quality():
    controls = models.VoiceControls(speed=1.0, pitch=0.0, volume=1.0, pause_ms=50)
    markup = ssml.build_ssml(
        "Salaam", language="ur", voice_id="rtas_ur_female_01", controls=controls
    )
    assert "<speak" in markup and "Salaam" in markup
    q = quality.score_quality(
        text="Natural speech sample for scoring",
        language="en",
        controls=controls,
        has_ssml=True,
    )
    assert q.overall >= 0.7
    assert q.grade in ("A", "B", "C", "D")


def test_generate_and_store():
    job = engine.generate_voice(
        "Welcome to RTAS Studio AI",
        language="en",
        gender="female",
        speed=1.05,
        enqueue=True,
        auto_process=True,
    )
    assert job.job_id.startswith("voicejob_")
    assert job.state == "completed"
    assert job.production_ready is True
    assert job.export.ready is True
    assert engine.get_job(job.job_id) is not None
    assert "rtas_en_female" in job.voice_id


def test_multilang_voices():
    for lang in ("en", "ur", "hi", "ar", "pa"):
        voices = presets.list_voices(language=lang)
        assert len(voices) >= 2
        job = engine.generate_voice(
            f"Test line for {lang}",
            language=lang,
            gender="male",
            auto_process=True,
        )
        assert job.language == lang
        assert job.state == "completed"


def test_queue_retry_cancel():
    q = queue_mod.voice_queue
    q.clear()
    job = engine.generate_voice(
        "Queue pending line",
        enqueue=True,
        auto_process=False,
    )
    assert job.state == "queued"
    processed = engine.process_voice_job(job.job_id)
    assert processed is not None and processed.state == "completed"

    processed.state = "failed"
    q.update_state(processed.job_id, "failed", error="forced")
    retried = q.retry(processed.job_id)
    assert retried.retry_count >= 1
    again = engine.process_voice_job(processed.job_id)
    assert again.state == "completed"

    pending = engine.generate_voice("Cancel me", enqueue=True, auto_process=False)
    cancelled = q.cancel(pending.job_id)
    assert cancelled.state == "cancelled"


if __name__ == "__main__":
    test_version()
    test_languages_pluggable()
    test_voice_validation()
    test_ssml_and_quality()
    test_generate_and_store()
    test_multilang_voices()
    test_queue_retry_cancel()
    print("OK voice_generation")

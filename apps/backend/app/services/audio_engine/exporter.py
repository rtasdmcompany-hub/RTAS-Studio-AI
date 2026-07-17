"""AudioExporter — export package metadata (no binary synthesis in Sprint 1)."""

from __future__ import annotations

from app.services.audio_engine.models import ExportPackage, ValidationResult


def build_export_package(
    job_id: str,
    *,
    validation: ValidationResult,
) -> ExportPackage:
    short = job_id.replace("audioeng_", "")[:8]
    ready = validation.passed
    notes = [
        "Sprint 1 ships planning + queue + metadata (synthesis providers pluggable).",
        "Primary delivery target: WAV 48kHz stereo; MP3/AAC alternates.",
    ]
    if not ready:
        notes.append("Export gated until validation passes.")
    return ExportPackage(
        ready=ready,
        formats=["wav", "mp3", "aac"],
        primary_format="wav",
        filename=f"rtas_audio_{short}.wav",
        notes=notes,
    )

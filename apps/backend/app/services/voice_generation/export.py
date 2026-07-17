"""Export package builder for generated voice."""

from __future__ import annotations

from app.services.voice_generation.models import VoiceExportPackage


def build_export(job_id: str, *, ready: bool) -> VoiceExportPackage:
    short = job_id.replace("voicejob_", "")[:8]
    notes = [
        "Sprint 2: simulation provider returns SSML + metadata; binary TTS providers are pluggable.",
        "Never logs provider API secrets.",
    ]
    if not ready:
        notes.append("Export gated until generation completes successfully.")
    return VoiceExportPackage(
        ready=ready,
        formats=["wav", "mp3", "ogg"],
        primary_format="wav",
        filename=f"rtas_voice_{short}.wav",
        ssml_included=True,
        notes=notes,
    )

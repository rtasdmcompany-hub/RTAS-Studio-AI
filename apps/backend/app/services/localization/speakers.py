"""Speaker detection, mapping, and voice identity preservation."""

from __future__ import annotations

from typing import Any

from app.services.localization.models import SpeakerMapEntry


def detect_speakers(
    text: str,
    *,
    character_memory: list[dict[str, Any]] | None = None,
    voice_summary: dict[str, Any] | None = None,
    clone_id: str | None = None,
) -> list[SpeakerMapEntry]:
    speakers: list[SpeakerMapEntry] = []
    chars = character_memory or []
    if chars:
        for i, c in enumerate(chars[:6]):
            if not isinstance(c, dict):
                continue
            cid = str(c.get("character_id") or f"Character_{i}")
            speakers.append(
                SpeakerMapEntry(
                    speaker_id=f"spk_{i}",
                    character_id=cid,
                    source_voice_id=str(
                        c.get("default_voice") or c.get("voice_id") or ""
                    )
                    or None,
                    clone_id=str(c.get("clone_id") or clone_id or "") or None,
                    gender=str(c.get("gender") or "unspecified"),
                    accent=str(c.get("accent") or "neutral"),
                    preserved=True,
                )
            )
    if not speakers:
        speakers.append(
            SpeakerMapEntry(
                speaker_id="spk_0",
                character_id=None,
                source_voice_id=(voice_summary or {}).get("voice_id"),
                clone_id=clone_id or (voice_summary or {}).get("clone_id"),
                gender=str((voice_summary or {}).get("gender") or "unspecified"),
                accent="neutral",
                preserved=True,
            )
        )
    # Heuristic: dialogue with quotes → second speaker
    if text.count('"') >= 2 and len(speakers) == 1:
        speakers.append(
            SpeakerMapEntry(
                speaker_id="spk_1",
                character_id=None,
                source_voice_id=None,
                clone_id=None,
                gender="unspecified",
                accent="neutral",
                preserved=True,
            )
        )
    return speakers

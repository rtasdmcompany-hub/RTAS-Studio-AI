"""SSML-ready text shaping (provider-agnostic)."""

from __future__ import annotations

import html
import re

from app.services.voice_generation.models import VoiceControls


def build_ssml(
    text: str,
    *,
    language: str,
    voice_id: str,
    controls: VoiceControls,
) -> str:
    """Produce SSML-ready markup; providers may consume or ignore tags."""
    safe = html.escape(text.strip())
    for word, tip in (controls.pronunciation_hints or {}).items():
        if not word or not tip:
            continue
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        safe = pattern.sub(
            f'<phoneme alphabet="ipa" ph="{html.escape(tip)}">{html.escape(word)}</phoneme>',
            safe,
            count=1,
        )

    rate_pct = int(round(controls.speed * 100))
    pitch = f"{controls.pitch:+.1f}st"
    volume_pct = int(round(max(0.0, min(2.0, controls.volume)) * 100))
    pause = max(0, int(controls.pause_ms))

    pause_tag = f'<break time="{pause}ms"/>' if pause > 0 else ""
    return (
        f'<speak version="1.0" xml:lang="{language}">'
        f'<voice name="{html.escape(voice_id)}">'
        f'<prosody rate="{rate_pct}%" pitch="{pitch}" volume="{volume_pct}%">'
        f"{pause_tag}{safe}"
        f"</prosody></voice></speak>"
    )

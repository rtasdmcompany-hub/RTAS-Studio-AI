"""Read uploaded audio duration for full-length music video stitching."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def probe_audio_duration_seconds(path: Path | None) -> float | None:
    """Return audio length in seconds, or None if unreadable."""
    if path is None or not path.is_file():
        return None

    suffix = path.suffix.lower()
    if suffix in (".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg"):
        mutagen_dur = _probe_mutagen(path)
        if mutagen_dur is not None:
            return mutagen_dur

    return _probe_ffprobe(path)


def _probe_mutagen(path: Path) -> float | None:
    try:
        from mutagen import File as MutagenFile
    except ImportError:
        return None

    try:
        audio = MutagenFile(str(path))
        if audio is None or audio.info is None:
            return None
        length = getattr(audio.info, "length", None)
        if length is None:
            return None
        seconds = float(length)
        return seconds if seconds > 0 else None
    except Exception as exc:
        logger.debug("mutagen probe failed for %s: %s", path.name, exc)
        return None


def _probe_ffprobe(path: Path) -> float | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            return None
        raw = (result.stdout or "").strip()
        seconds = float(raw)
        return seconds if seconds > 0 else None
    except Exception as exc:
        logger.debug("ffprobe probe failed for %s: %s", path.name, exc)
        return None

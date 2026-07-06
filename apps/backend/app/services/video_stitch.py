"""FFmpeg — concatenate Fal clips and mux uploaded audio for full-length exports."""

from __future__ import annotations

import logging
import subprocess
import textwrap
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoStitchError(Exception):
    pass


def stitch_clips_with_audio(
    clip_paths: list[Path],
    output_path: Path,
    audio_path: Path | None = None,
    target_duration_sec: float | None = None,
) -> Path:
    """Merge sequential MP4 clips; optionally mux audio trimmed to target duration."""
    if not clip_paths:
        raise VideoStitchError("No video clips to stitch")

    missing = [p.name for p in clip_paths if not p.is_file()]
    if missing:
        raise VideoStitchError(f"Missing clip file(s) for stitch: {', '.join(missing)}")

    ordered = list(clip_paths)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    work_dir = output_path.parent / f"{output_path.stem}_stitch_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    concat_list = work_dir / "concat.txt"
    concat_lines = "\n".join(
        f"file '{p.resolve().as_posix()}'" for p in ordered if p.is_file()
    )
    concat_list.write_text(concat_lines, encoding="utf-8")

    stitched_silent = work_dir / "stitched_silent.mp4"
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(stitched_silent),
        ],
        "concat clips",
    )

    if audio_path and audio_path.is_file():
        duration_args: list[str] = []
        if target_duration_sec and target_duration_sec > 0:
            duration_args = ["-t", str(round(target_duration_sec, 3))]

        _run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(stitched_silent),
                "-i",
                str(audio_path),
                *duration_args,
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                str(output_path),
            ],
            "mux audio",
        )
    else:
        if target_duration_sec and target_duration_sec > 0:
            _run_ffmpeg(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(stitched_silent),
                    "-t",
                    str(round(target_duration_sec, 3)),
                    "-c",
                    "copy",
                    str(output_path),
                ],
                "trim stitched video",
            )
        else:
            stitched_silent.replace(output_path)

    if not output_path.is_file():
        raise VideoStitchError("Stitched output file was not created")

    logger.info(
        "Stitched %s clips → %s (audio=%s)",
        len(clip_paths),
        output_path.name,
        audio_path.name if audio_path else "none",
    )
    return output_path


def _run_ffmpeg(args: list[str], label: str) -> None:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
    except FileNotFoundError as exc:
        raise VideoStitchError(
            "FFmpeg is not installed. Install ffmpeg and add it to PATH, then restart the API."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise VideoStitchError(f"FFmpeg timed out during {label}") from exc

    if result.returncode != 0:
        stderr = (result.stderr or result.stdout or "").strip()
        snippet = textwrap.shorten(stderr, width=400, placeholder="…")
        raise VideoStitchError(f"FFmpeg failed ({label}): {snippet}")

"""
FFmpeg video stitcher — merge short generated clips into one ~5-minute export.

Used by apps/web/src/app/api/compile/route.ts via CLI or direct import.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import textwrap
from pathlib import Path

logger = logging.getLogger(__name__)

TARGET_DURATION_SEC = 300.0  # 5 minutes


class VideoStitcherError(Exception):
    """Raised when stitching fails (missing files, FFmpeg error, etc.)."""


def stitch_videos(
    video_list: list[str | Path],
    output_path: str | Path,
    *,
    target_duration_sec: float = TARGET_DURATION_SEC,
) -> Path:
    """
    Merge sequential MP4 clips into a single file (default cap: 5 minutes).

    Args:
        video_list: Ordered paths to source clips.
        output_path: Destination MP4 path.
        target_duration_sec: Trim stitched output to this length (seconds).

    Returns:
        Resolved path to the written output file.
    """
    clips = [_resolve_clip(path) for path in video_list]
    if not clips:
        raise VideoStitcherError("video_list is empty — nothing to stitch")

    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    work_dir = out.parent / f"{out.stem}_stitch_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    concat_list = work_dir / "concat.txt"
    concat_list.write_text(
        "\n".join(f"file '{clip.as_posix()}'" for clip in clips),
        encoding="utf-8",
    )

    stitched_raw = work_dir / "stitched_raw.mp4"
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
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(stitched_raw),
        ],
        "concat clips",
    )

    if target_duration_sec > 0:
        _run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(stitched_raw),
                "-t",
                str(round(target_duration_sec, 3)),
                "-c",
                "copy",
                str(out),
            ],
            "trim to target duration",
        )
    else:
        stitched_raw.replace(out)

    if not out.is_file():
        raise VideoStitcherError(f"Stitched output was not created: {out}")

    logger.info(
        "Stitched %s clips → %s (target %.0fs)",
        len(clips),
        out.name,
        target_duration_sec,
    )
    return out


def _resolve_clip(path: str | Path) -> Path:
    clip = Path(path).resolve()
    if not clip.is_file():
        raise VideoStitcherError(f"Clip not found: {clip}")
    if clip.suffix.lower() not in {".mp4", ".mov", ".webm", ".mkv"}:
        raise VideoStitcherError(f"Unsupported clip format: {clip.name}")
    return clip


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
        raise VideoStitcherError(
            "FFmpeg is not installed. Install ffmpeg and add it to PATH."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise VideoStitcherError(f"FFmpeg timed out during {label}") from exc

    if result.returncode != 0:
        stderr = (result.stderr or result.stdout or "").strip()
        snippet = textwrap.shorten(stderr, width=400, placeholder="…")
        raise VideoStitcherError(f"FFmpeg failed ({label}): {snippet}")


def _default_outputs_dir() -> Path:
    return Path(__file__).resolve().parent / "data" / "outputs"


def scan_output_clips(outputs_dir: Path | None = None) -> list[Path]:
    """Return MP4 clips in outputs dir, oldest first."""
    root = (outputs_dir or _default_outputs_dir()).resolve()
    if not root.is_dir():
        return []
    clips = sorted(
        (
            p
            for p in root.glob("*.mp4")
            if p.is_file()
            and "_compiled" not in p.stem
            and not p.name.startswith("compiled_5min")
        ),
        key=lambda p: p.stat().st_mtime,
    )
    return clips


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Merge RTAS output clips with FFmpeg")
    parser.add_argument(
        "--inputs",
        nargs="*",
        help="Explicit clip paths (default: scan data/outputs/*.mp4)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output MP4 path",
    )
    parser.add_argument(
        "--outputs-dir",
        default=str(_default_outputs_dir()),
        help="Directory to scan when --inputs omitted",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=TARGET_DURATION_SEC,
        help="Target duration in seconds (default: 300)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.inputs:
        clips = [Path(p) for p in args.inputs]
    else:
        clips = scan_output_clips(Path(args.outputs_dir))

    try:
        result_path = stitch_videos(clips, args.output, target_duration_sec=args.duration)
    except VideoStitcherError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "ok": True,
                "output": str(result_path),
                "clip_count": len(clips),
                "target_duration_sec": args.duration,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

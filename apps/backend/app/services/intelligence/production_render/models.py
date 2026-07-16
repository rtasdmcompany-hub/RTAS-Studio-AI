"""Models for Production Render & Export Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

AspectRatio = Literal["vertical", "landscape", "square"]
ContainerFormat = Literal["mp4", "mov", "webm"]
ResolutionTier = Literal["720p", "1080p", "4k", "8k_ready"]


@dataclass
class ExportSpec:
    format: ContainerFormat
    aspect: AspectRatio
    resolution: ResolutionTier
    hdr: bool
    fps: int
    audio_channels: str
    codec_video: str
    codec_audio: str
    bitrate_hint_mbps: float
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SubtitleCue:
    index: int
    start_sec: float
    end_sec: float
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ThumbnailInstruction:
    timestamp_sec: float
    framing: str
    subject: str
    mood: str
    text_safe_area: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AssetRef:
    asset_id: str
    kind: str
    label: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationIssue:
    code: str
    severity: Literal["error", "warning", "info"]
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExportValidation:
    passed: bool
    score: float
    issues: list[ValidationIssue] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score,
            "issues": [i.to_dict() for i in self.issues],
            "checks": self.checks,
        }


@dataclass
class VideoManifest:
    version: str
    title: str
    runtime_seconds: float
    scenes: int
    shots: int
    tracks: dict[str, Any]
    export: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProductionRenderPackage:
    """Final combined production package for render/export."""

    json_package: dict[str, Any]
    timeline: dict[str, Any]
    assets: list[AssetRef]
    video_manifest: VideoManifest
    subtitle_file: str  # SRT content
    captions: list[SubtitleCue]
    thumbnail_instructions: list[ThumbnailInstruction]
    voice_package: dict[str, Any]
    music_package: dict[str, Any]
    camera_plan: list[dict[str, Any]]
    director_notes: list[str]
    effects: list[dict[str, Any]]
    transitions: list[dict[str, Any]]
    export_specs: list[ExportSpec]
    validation: ExportValidation
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "json_package": self.json_package,
            "timeline": self.timeline,
            "assets": [a.to_dict() for a in self.assets],
            "video_manifest": self.video_manifest.to_dict(),
            "subtitle_file": self.subtitle_file,
            "captions": [c.to_dict() for c in self.captions],
            "thumbnail_instructions": [t.to_dict() for t in self.thumbnail_instructions],
            "voice_package": self.voice_package,
            "music_package": self.music_package,
            "camera_plan": self.camera_plan,
            "director_notes": self.director_notes,
            "effects": self.effects,
            "transitions": self.transitions,
            "export_specs": [e.to_dict() for e in self.export_specs],
            "validation": self.validation.to_dict(),
            "metadata": self.metadata,
        }

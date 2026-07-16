"""Asset inventory for the production package."""

from __future__ import annotations

from typing import Any

from app.services.intelligence.production_render.models import AssetRef


def build_asset_inventory(
    *,
    scenes: list[dict[str, Any]],
    shots: list[dict[str, Any]],
    character_memory: list[dict[str, Any]],
    audio_director: dict[str, Any] | None,
    understanding: dict[str, Any] | None,
) -> list[AssetRef]:
    assets: list[AssetRef] = []

    for i, scene in enumerate(scenes):
        sid = f"scene_{scene.get('index', i)}"
        assets.append(
            AssetRef(
                asset_id=sid,
                kind="scene",
                label=str(scene.get("title") or sid),
                source="scene_planner",
                metadata={
                    "duration_seconds": scene.get("duration_seconds"),
                    "environment": scene.get("environment"),
                },
            )
        )

    for i, shot in enumerate(shots):
        shid = f"shot_{shot.get('scene_index', 0)}_{shot.get('shot_index', i)}"
        assets.append(
            AssetRef(
                asset_id=shid,
                kind="shot",
                label=str(shot.get("title") or shid),
                source="shot_generator",
                metadata={
                    "camera": shot.get("camera"),
                    "duration_seconds": shot.get("duration_seconds"),
                },
            )
        )

    for char in character_memory:
        cid = str(char.get("character_id") or "character")
        assets.append(
            AssetRef(
                asset_id=f"character_{cid}",
                kind="character",
                label=cid,
                source="character_memory",
                metadata={
                    "face_embedding_ref": char.get("face_embedding_ref"),
                    "reference_image_urls": char.get("reference_image_urls") or [],
                    "outfit": char.get("outfit"),
                },
            )
        )

    if audio_director:
        assets.append(
            AssetRef(
                asset_id="audio_voice_pack",
                kind="voice",
                label="Voice / narration package",
                source="audio_director",
                metadata={"cues": len(audio_director.get("voice_timeline") or [])},
            )
        )
        assets.append(
            AssetRef(
                asset_id="audio_music_pack",
                kind="music",
                label="Music package",
                source="audio_director",
                metadata={"cues": len(audio_director.get("music_timeline") or [])},
            )
        )
        assets.append(
            AssetRef(
                asset_id="audio_sfx_pack",
                kind="sfx",
                label="SFX / ambient / foley",
                source="audio_director",
                metadata={"cues": len(audio_director.get("sfx_timeline") or [])},
            )
        )

    if understanding:
        assets.append(
            AssetRef(
                asset_id="prompt_understanding",
                kind="metadata",
                label="Cinematic prompt understanding",
                source="prompt_understanding",
                metadata={
                    "category": understanding.get("category"),
                    "mood": understanding.get("mood"),
                },
            )
        )

    assets.append(
        AssetRef(
            asset_id="subtitles_srt",
            kind="subtitle",
            label="Subtitles (SRT)",
            source="production_render",
            metadata={"format": "srt"},
        )
    )
    return assets

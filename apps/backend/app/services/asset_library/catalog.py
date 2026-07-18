"""Asset types, categories, and permission roles."""

from __future__ import annotations

from typing import Final

ASSET_TYPES: Final[tuple[str, ...]] = (
    "image",
    "video",
    "audio",
    "music",
    "voice",
    "document",
    "prompt",
    "character",
    "ai_model",
    "template",
    "brand",
    "logo",
    "thumbnail",
)

ASSET_STATUSES: Final[tuple[str, ...]] = (
    "active",
    "archived",
    "deleted",
)

PERMISSION_ROLES: Final[tuple[str, ...]] = ("owner", "edit", "read")

SYSTEM_CATEGORIES: Final[list[dict]] = [
    {"key": "general", "name": "General"},
    {"key": "production", "name": "Production"},
    {"key": "brand", "name": "Brand"},
    {"key": "characters", "name": "Characters"},
    {"key": "audio", "name": "Audio"},
    {"key": "video", "name": "Video"},
    {"key": "templates", "name": "Templates"},
    {"key": "ai", "name": "AI Assets"},
]

ROLE_RANK = {"read": 1, "edit": 2, "owner": 3}


def normalize_asset_type(value: str) -> str:
    key = value.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "images": "image",
        "videos": "video",
        "voice_files": "voice",
        "voices": "voice",
        "documents": "document",
        "prompts": "prompt",
        "characters": "character",
        "models": "ai_model",
        "ai_models": "ai_model",
        "templates": "template",
        "brand_assets": "brand",
        "logos": "logo",
        "thumbnails": "thumbnail",
    }
    key = aliases.get(key, key)
    if key not in ASSET_TYPES:
        raise ValueError(f"unsupported asset type: {value}")
    return key


def role_at_least(role: str, required: str) -> bool:
    return ROLE_RANK.get(role, 0) >= ROLE_RANK.get(required, 99)

"""RTAS Studio AI — Music Generation & Composition Engine (Phase 4 Sprint 4)."""

from app.services.music_generation.engine import (
    generate_music,
    generate_music_dict,
    get_job,
    process_music_job,
    version_payload,
)
from app.services.music_generation.genres import list_genres, register_genre
from app.services.music_generation.instruments import list_instruments, register_instrument
from app.services.music_generation.library import library_payload
from app.services.music_generation.queue import music_queue
from app.services.music_generation import store
from app.services.music_generation.video_bridge import adapt_from_video_context
from app.services.music_generation.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION

__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "generate_music",
    "generate_music_dict",
    "get_job",
    "process_music_job",
    "version_payload",
    "library_payload",
    "list_genres",
    "list_instruments",
    "register_genre",
    "register_instrument",
    "adapt_from_video_context",
    "music_queue",
    "store",
]

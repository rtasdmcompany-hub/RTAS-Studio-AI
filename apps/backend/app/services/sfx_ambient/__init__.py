"""RTAS Studio AI — Sound Effects & Ambient Audio Engine (Phase 4 Sprint 5)."""

from app.services.sfx_ambient.categories import (
    list_categories,
    register_category,
    recommend_for_mood,
)
from app.services.sfx_ambient.engine import (
    generate_ambient,
    generate_ambient_dict,
    generate_scene_audio_dict,
    generate_sfx,
    generate_sfx_ambient,
    generate_sfx_dict,
    get_job,
    process_sfx_job,
)
from app.services.sfx_ambient.library import (
    ambient_catalog_payload,
    library_payload,
    sfx_catalog_payload,
)
from app.services.sfx_ambient.queue import sfx_queue
from app.services.sfx_ambient.scene_intelligence import (
    build_environment_profile,
    detect_environment,
)
from app.services.sfx_ambient import store
from app.services.sfx_ambient.video_bridge import adapt_from_video_context
from app.services.sfx_ambient.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION

__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "generate_sfx_ambient",
    "generate_sfx",
    "generate_ambient",
    "generate_sfx_dict",
    "generate_ambient_dict",
    "generate_scene_audio_dict",
    "get_job",
    "process_sfx_job",
    "library_payload",
    "sfx_catalog_payload",
    "ambient_catalog_payload",
    "list_categories",
    "register_category",
    "recommend_for_mood",
    "build_environment_profile",
    "detect_environment",
    "adapt_from_video_context",
    "sfx_queue",
    "store",
]

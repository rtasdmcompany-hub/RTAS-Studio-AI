"""RTAS Studio AI — AI Character Motion & Cinematic Animation Engine (Phase 5 Sprint 5)."""

from app.services.character_motion.engine import (
    create_dict,
    create_motion_job,
    generate_dict,
    generate_motion,
    get_motion,
    motion_history,
    motion_library_payload,
    process_motion_job,
)
from app.services.character_motion import store
from app.services.character_motion.library import register_action
from app.services.character_motion.models import BODY_PRESERVED_TRAITS
from app.services.character_motion.queue import motion_queue
from app.services.character_motion.version import (
    BODY_CONSISTENCY_THRESHOLD,
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
)

__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "BODY_CONSISTENCY_THRESHOLD",
    "BODY_PRESERVED_TRAITS",
    "create_motion_job",
    "create_dict",
    "generate_motion",
    "generate_dict",
    "get_motion",
    "motion_history",
    "motion_library_payload",
    "process_motion_job",
    "register_action",
    "motion_queue",
    "store",
]

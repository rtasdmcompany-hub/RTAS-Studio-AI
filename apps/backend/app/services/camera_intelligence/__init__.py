"""RTAS Studio AI — AI Cinematic Camera & Shot Intelligence Engine (Phase 5 Sprint 6)."""

from app.services.camera_intelligence.engine import (
    camera_history,
    camera_library_payload,
    generate_camera,
    generate_dict,
    get_camera,
    plan_camera,
    plan_dict,
    process_camera_job,
)
from app.services.camera_intelligence import store
from app.services.camera_intelligence.library import register_shot
from app.services.camera_intelligence.queue import camera_queue
from app.services.camera_intelligence.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION

__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "plan_camera",
    "plan_dict",
    "generate_camera",
    "generate_dict",
    "get_camera",
    "camera_history",
    "camera_library_payload",
    "process_camera_job",
    "register_shot",
    "camera_queue",
    "store",
]

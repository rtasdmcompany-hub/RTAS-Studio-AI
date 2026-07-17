"""RTAS Studio AI Audio Production Engine — public API (Phase 4 Sprint 1)."""

from app.services.audio_engine.engine import (
    build_audio_engine_dict,
    build_audio_engine_plan,
    get_plan,
)
from app.services.audio_engine.models import AudioEnginePlan
from app.services.audio_engine.queue import audio_queue
from app.services.audio_engine.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION

__all__ = [
    "AudioEnginePlan",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "audio_queue",
    "build_audio_engine_dict",
    "build_audio_engine_plan",
    "get_plan",
]

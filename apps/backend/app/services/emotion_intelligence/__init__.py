"""RTAS Studio AI — AI Emotion, Expression & Performance Engine (Phase 5 Sprint 7)."""

from app.services.emotion_intelligence.engine import (
    analyze_dict,
    analyze_emotion,
    emotion_history,
    emotion_library_payload,
    generate_dict,
    generate_emotion,
    get_emotion,
    process_emotion_job,
)
from app.services.emotion_intelligence import store, memory
from app.services.emotion_intelligence.library import register_emotion
from app.services.emotion_intelligence.queue import emotion_queue
from app.services.emotion_intelligence.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION

__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "analyze_emotion",
    "analyze_dict",
    "generate_emotion",
    "generate_dict",
    "get_emotion",
    "emotion_history",
    "emotion_library_payload",
    "process_emotion_job",
    "register_emotion",
    "emotion_queue",
    "store",
    "memory",
]

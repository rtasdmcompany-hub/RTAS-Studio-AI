"""RTAS Studio AI — Multi-Language Dubbing & Localization Engine (Phase 4 Sprint 7)."""

from app.services.localization.engine import (
    dub,
    dub_dict,
    get_job,
    languages_payload,
    localize,
    localize_dict,
    process_localization_job,
    translate,
    translate_dict,
)
from app.services.localization.languages import list_languages, register_language
from app.services.localization.queue import localization_queue
from app.services.localization import store
from app.services.localization.translation import memory_clear, memory_size
from app.services.localization.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION

__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "localize",
    "translate",
    "dub",
    "localize_dict",
    "translate_dict",
    "dub_dict",
    "get_job",
    "process_localization_job",
    "languages_payload",
    "list_languages",
    "register_language",
    "localization_queue",
    "store",
    "memory_clear",
    "memory_size",
]

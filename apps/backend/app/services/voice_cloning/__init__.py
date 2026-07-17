"""RTAS Studio AI — Voice Cloning & Character Voice Engine (Phase 4 Sprint 3)."""

from app.services.voice_cloning.character_bridge import (
    assign_clone_to_character,
    enrich_character_memory_dicts,
    profile_from_character_memory,
    restore_voice_for_generation,
)
from app.services.voice_cloning.engine import (
    clone_voice,
    clone_voice_dict,
    get_clone,
    lock_clone_voice,
    preview_clone,
    process_clone_job,
    retrain_clone,
    switch_character_voice,
)
from app.services.voice_cloning.queue import clone_queue
from app.services.voice_cloning import store
from app.services.voice_cloning.security import list_audit, verify_signature
from app.services.voice_cloning.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION

__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "clone_voice",
    "clone_voice_dict",
    "get_clone",
    "process_clone_job",
    "retrain_clone",
    "lock_clone_voice",
    "switch_character_voice",
    "preview_clone",
    "assign_clone_to_character",
    "profile_from_character_memory",
    "restore_voice_for_generation",
    "enrich_character_memory_dicts",
    "clone_queue",
    "store",
    "list_audit",
    "verify_signature",
]

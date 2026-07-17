"""RTAS Studio AI — AI Avatar & Character Generation Engine (Phase 5 Sprint 1)."""

from app.services.character_generation.engine import (
    create_character,
    create_character_dict,
    get_avatar_payload,
    get_character,
    get_job,
    list_characters,
)
from app.services.character_generation.paddle_status import paddle_status
from app.services.character_generation.registry import registry_payload
from app.services.character_generation.templates import list_templates
from app.services.character_generation import store, registry
from app.services.character_generation.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION

__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "create_character",
    "create_character_dict",
    "get_character",
    "get_job",
    "get_avatar_payload",
    "list_characters",
    "list_templates",
    "paddle_status",
    "registry_payload",
    "store",
    "registry",
]

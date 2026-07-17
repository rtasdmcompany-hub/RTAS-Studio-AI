"""RTAS Studio AI Voice Generation Engine — public API."""

from app.services.voice_generation.engine import (
    generate_voice,
    generate_voice_dict,
    get_job,
    process_voice_job,
)
from app.services.voice_generation.models import VoiceGenerationJob
from app.services.voice_generation.presets import list_voices, voices_payload
from app.services.voice_generation.queue import voice_queue
from app.services.voice_generation import store
from app.services.voice_generation.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION

__all__ = [
    "VoiceGenerationJob",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "voice_queue",
    "generate_voice",
    "generate_voice_dict",
    "get_job",
    "process_voice_job",
    "list_voices",
    "voices_payload",
    "store",
]

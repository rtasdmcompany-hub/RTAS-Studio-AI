"""Single-flight guard — only one live generation at a time (protects Fal wallet)."""

from __future__ import annotations

import asyncio

_lock = asyncio.Lock()
_in_progress = False


async def acquire_generation_slot() -> None:
    global _in_progress
    async with _lock:
        if _in_progress:
            raise GenerationInProgressError()
        _in_progress = True


async def release_generation_slot() -> None:
    global _in_progress
    async with _lock:
        _in_progress = False


class GenerationInProgressError(Exception):
    """Raised when a second POST /api/generate arrives while one is running."""

    message = "A video generation is already in progress. Please wait for it to finish."

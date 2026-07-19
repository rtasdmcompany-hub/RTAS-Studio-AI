"""Agent types, workflow modes, scheduler policies, and orchestration constants."""

from __future__ import annotations

import re
from typing import Final

AGENT_TYPES: Final[tuple[str, ...]] = (
    "director",
    "prompt_engineer",
    "script_writer",
    "storyboard",
    "scene_planner",
    "camera_director",
    "character_director",
    "voice_director",
    "music_director",
    "video_director",
    "qa",
    "custom",
)

AGENT_STATUSES: Final[tuple[str, ...]] = ("active", "paused", "disabled", "archived")

WORKFLOW_TRIGGERS: Final[tuple[str, ...]] = (
    "manual",
    "schedule",
    "event",
    "webhook",
    "api",
)

TASK_MODES: Final[tuple[str, ...]] = ("sequential", "parallel", "conditional")

EXECUTION_STATUSES: Final[tuple[str, ...]] = (
    "queued",
    "running",
    "completed",
    "failed",
    "cancelled",
    "retrying",
)

SCHEDULE_KINDS: Final[tuple[str, ...]] = (
    "once",
    "recurring",
    "daily",
    "weekly",
    "monthly",
)

JOB_PRIORITIES: Final[tuple[str, ...]] = ("low", "normal", "high", "critical")

DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_MEMORY_LIMIT: Final[int] = 100

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    slug = _SLUG_RE.sub("-", (value or "").lower()).strip("-")
    return slug or "agent"


def agent_capabilities(agent_type: str) -> list[str]:
    base = {
        "director": ["orchestrate", "delegate", "review"],
        "prompt_engineer": ["prompt.optimize", "prompt.validate"],
        "script_writer": ["script.write", "dialogue.generate"],
        "storyboard": ["storyboard.plan", "shot.list"],
        "scene_planner": ["scene.plan", "blocking"],
        "camera_director": ["camera.plan", "lens.select"],
        "character_director": ["character.direct", "performance.guide"],
        "voice_director": ["voice.direct", "dialogue.timing"],
        "music_director": ["music.select", "score.plan"],
        "video_director": ["video.compose", "cut.plan"],
        "qa": ["qa.check", "quality.score"],
        "custom": ["custom.execute"],
    }
    return list(base.get(agent_type, base["custom"]))


def default_workflow_templates() -> list[dict]:
    return [
        {
            "slug": "full-production",
            "name": "Full Production Pipeline",
            "description": "Director-led multi-agent production from prompt to QA",
            "mode": "sequential",
            "agentTypes": [
                "prompt_engineer",
                "script_writer",
                "storyboard",
                "scene_planner",
                "camera_director",
                "video_director",
                "qa",
            ],
        },
        {
            "slug": "script-to-storyboard",
            "name": "Script to Storyboard",
            "description": "Parallel script and storyboard collaboration",
            "mode": "parallel",
            "agentTypes": ["script_writer", "storyboard", "scene_planner"],
        },
        {
            "slug": "audio-pass",
            "name": "Audio Direction Pass",
            "description": "Voice and music directors with QA gate",
            "mode": "sequential",
            "agentTypes": ["voice_director", "music_director", "qa"],
        },
    ]

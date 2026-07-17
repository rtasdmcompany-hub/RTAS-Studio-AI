"""Voice & Dialogue Intelligence Engine — public operations."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from app.services.voice_intelligence import store
from app.services.voice_intelligence.consistency import verify_consistency
from app.services.voice_intelligence.dialogue_planner import dialogue_role_summary, plan_dialogue
from app.services.voice_intelligence.models import VoiceIntelligenceJob
from app.services.voice_intelligence.narration import build_narration_summary
from app.services.voice_intelligence.timing import apply_timing
from app.services.voice_intelligence.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION
from app.services.voice_intelligence.voice_manager import (
    apply_manual_assignments,
    assign_voices,
)


def _project_id(script: str, explicit: str | None = None) -> str:
    if explicit and explicit.strip():
        return explicit.strip()
    digest = hashlib.sha1(f"{script}|{time.time_ns()}".encode()).hexdigest()
    return f"vproj_{digest[:12]}"


def _job_id(project_id: str) -> str:
    digest = hashlib.sha1(f"vjob|{project_id}|{ENGINE_VERSION}".encode()).hexdigest()
    return f"vintel_{digest[:12]}"


def analyze_script(
    script: str,
    *,
    project_id: str | None = None,
    language: str = "en",
    assignments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    text = (script or "").strip()
    if not text:
        raise ValueError("script is required")
    pid = _project_id(text, project_id)
    existing = store.get_by_project(pid)
    lines = plan_dialogue(text, project_id=pid)
    profiles = assign_voices(lines, language=language)
    if assignments:
        profiles = apply_manual_assignments(profiles, assignments, language=language)
        # Re-stamp voice ids on lines after manual assign
        for ln in lines:
            if ln.role in profiles:
                ln.voice_id = profiles[ln.role].voice_id
                if profiles[ln.role].character_slot:
                    ln.character_slot = profiles[ln.role].character_slot

    speeds = {
        **{role: p.speaking_speed for role, p in profiles.items()},
        **{
            (p.character_slot or role): p.speaking_speed
            for role, p in profiles.items()
        },
    }
    timing = apply_timing(lines, speaking_speeds=speeds)
    narration = build_narration_summary(lines)
    consistency = verify_consistency(pid, lines, profiles)

    job = VoiceIntelligenceJob(
        project_id=pid,
        job_id=existing.job_id if existing else _job_id(pid),
        script=text,
        language=(language or "en").split("-")[0].lower(),
        lines=lines,
        voice_profiles=profiles,
        timing=timing,
        narration_summary=narration,
        consistency=consistency,
        version=(existing.version + 1) if existing else 1,
        production_ready=True,
        metadata={
            "engine_version": ENGINE_VERSION,
            "analyzed_at": time.time(),
            "role_summary": dialogue_role_summary(lines),
        },
    )
    store.save(job)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "operation": "analyze",
        **job.to_dict(),
    }


def assign_project_voices(
    project_id: str,
    *,
    assignments: list[dict[str, Any]] | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    job = store.get_by_project(project_id)
    if not job:
        raise ValueError(f"Project not found: {project_id}. Run /analyze first.")
    lang = language or job.language
    profiles = apply_manual_assignments(job.voice_profiles, assignments, language=lang)
    for ln in job.lines:
        if ln.role in profiles:
            ln.voice_id = profiles[ln.role].voice_id
    speeds = {role: p.speaking_speed for role, p in profiles.items()}
    job.voice_profiles = profiles
    job.timing = apply_timing(job.lines, speaking_speeds=speeds)
    job.narration_summary = build_narration_summary(job.lines)
    job.consistency = verify_consistency(job.project_id, job.lines, profiles)
    job.version += 1
    job.metadata["assigned_at"] = time.time()
    store.save(job)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "operation": "assign",
        **job.to_dict(),
    }


def synchronize_project(project_id: str) -> dict[str, Any]:
    job = store.get_by_project(project_id)
    if not job:
        raise ValueError(f"Project not found: {project_id}. Run /analyze first.")
    # Re-apply voice stamps + timing to guarantee sync
    for ln in job.lines:
        profile = job.voice_profiles.get(ln.role)
        if profile:
            ln.voice_id = profile.voice_id
    speeds = {role: p.speaking_speed for role, p in job.voice_profiles.items()}
    job.timing = apply_timing(job.lines, speaking_speeds=speeds)
    job.narration_summary = build_narration_summary(job.lines)
    job.consistency = verify_consistency(job.project_id, job.lines, job.voice_profiles)
    job.version += 1
    job.metadata["synchronized_at"] = time.time()
    store.save(job)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "operation": "synchronize",
        "synchronized": True,
        **job.to_dict(),
    }


def get_project(project_id: str) -> dict[str, Any] | None:
    job = store.get_by_project(project_id)
    if not job:
        return None
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        **job.to_dict(),
    }


def analyze_dict(**kwargs: Any) -> dict[str, Any]:
    return analyze_script(**kwargs)


def assign_dict(**kwargs: Any) -> dict[str, Any]:
    return assign_project_voices(**kwargs)


def synchronize_dict(**kwargs: Any) -> dict[str, Any]:
    return synchronize_project(**kwargs)

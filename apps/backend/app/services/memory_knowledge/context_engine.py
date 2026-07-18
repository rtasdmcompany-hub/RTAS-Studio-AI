"""Context Engine — continuity across prompts, story, character, scene, camera, audio."""

from __future__ import annotations

from typing import Any

from app.services.memory_knowledge import cache, metrics, security, store
from app.services.memory_knowledge.models import ContextRecord, TimelineEntry, new_id


def load_context(
    *,
    user_id: str,
    project_id: str | None = None,
    prompt: str | None = None,
    output: str | None = None,
    story: dict[str, Any] | None = None,
    character: dict[str, Any] | None = None,
    scene: dict[str, Any] | None = None,
    camera: dict[str, Any] | None = None,
    audio: dict[str, Any] | None = None,
    environment: dict[str, Any] | None = None,
    workflow: dict[str, Any] | None = None,
    memory_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Load or create/update project context; reconstruct continuity bundle."""
    uid = security.assert_user(user_id)
    t0 = metrics.timed()
    cache_key = f"ctx:{uid}:{project_id}"
    existing = None
    if project_id:
        store.register_project_member(project_id, uid)
        existing = store.context_for_project(uid, project_id)

    if existing is None:
        existing = ContextRecord(
            context_id=new_id("ctx"),
            user_id=uid,
            project_id=project_id,
        )

    if prompt:
        existing.previous_prompts.append(prompt)
        existing.previous_prompts = existing.previous_prompts[-50:]
    if output:
        existing.previous_outputs.append(output)
        existing.previous_outputs = existing.previous_outputs[-50:]
    if story:
        existing.story_continuity.update(story)
    if character:
        existing.character_continuity.update(character)
    if scene:
        existing.scene_continuity.update(scene)
    if camera:
        existing.camera_continuity.update(camera)
    if audio:
        existing.audio_continuity.update(audio)
    if environment:
        existing.environment_continuity.update(environment)
    if workflow:
        existing.user_workflow.update(workflow)
    if memory_refs:
        for mid in memory_refs:
            if mid not in existing.memory_refs:
                existing.memory_refs.append(mid)
        existing.memory_refs = existing.memory_refs[-200:]

    from datetime import datetime, timezone

    existing.updated_at = datetime.now(timezone.utc).isoformat()
    store.save_context(existing)
    store.add_timeline(
        TimelineEntry(
            entry_id=new_id("tl"),
            user_id=uid,
            project_id=project_id,
            event_type="context.load",
            summary="context updated",
            ref_id=existing.context_id,
        )
    )

    # Pull related memories for reconstruction
    related = []
    if project_id:
        related = [
            m.to_dict()
            for m in store.memories_for(user_id=uid, project_id=project_id)[:30]
        ]

    # Context accuracy: how many continuity channels are populated
    channels = [
        existing.story_continuity,
        existing.character_continuity,
        existing.scene_continuity,
        existing.camera_continuity,
        existing.audio_continuity,
        existing.environment_continuity,
        existing.user_workflow,
        existing.previous_prompts,
    ]
    filled = sum(1 for c in channels if c)
    accuracy = filled / len(channels)
    metrics.record_context_accuracy(accuracy)
    metrics.record_retrieval(metrics.elapsed_ms(t0))

    payload = {
        "ok": True,
        "context": existing.to_dict(),
        "reconstructed": {
            "prompts": list(existing.previous_prompts[-10:]),
            "outputs": list(existing.previous_outputs[-10:]),
            "story": existing.story_continuity,
            "character": existing.character_continuity,
            "scene": existing.scene_continuity,
            "camera": existing.camera_continuity,
            "audio": existing.audio_continuity,
            "environment": existing.environment_continuity,
            "workflow": existing.user_workflow,
            "related_memories": related,
        },
        "context_accuracy": round(accuracy * 100.0, 2),
    }
    cache.set(cache_key, payload)
    security.audit(
        uid, "load", "context", existing.context_id, project_id=project_id
    )
    return payload

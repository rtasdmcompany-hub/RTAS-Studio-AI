"""Character Generation Engine — create, recall, list."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from app.services.character_generation import registry, store
from app.services.character_generation.models import (
    CharacterJob,
    CharacterMetadata,
    CharacterRecord,
)
from app.services.character_generation.paddle_status import paddle_status
from app.services.character_generation.templates import (
    build_dna,
    build_identity,
    get_template,
    list_templates,
)
from app.services.character_generation.validation import validate_create_request
from app.services.character_generation.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PROVIDER_SIMULATION,
)


def _job_id(*parts: str) -> str:
    digest = hashlib.sha1(
        ("|".join(parts) + f"|{ENGINE_VERSION}").encode()
    ).hexdigest()
    return f"avatar_{digest[:10]}"


def _character_id(unique_seed: str) -> str:
    digest = hashlib.sha1(f"{unique_seed}|{ENGINE_VERSION}".encode()).hexdigest()
    return f"char_{digest[:12]}"


def _unique_id(seed: str) -> str:
    digest = hashlib.sha1(f"uid|{seed}|{time.time_ns()}".encode()).hexdigest()
    return f"cuid_{digest[:16]}"


def create_character(
    *,
    name: str | None = None,
    prompt: str | None = None,
    template_id: str | None = None,
    registry_slot: str | None = None,
    gender: str | None = None,
    age: int | None = None,
    ethnicity: str | None = None,
    body_type: str | None = None,
    hairstyle: str | None = None,
    beard: str | None = None,
    skin: str | None = None,
    eye_color: str | None = None,
    clothing: str | None = None,
    accessories: list[str] | None = None,
    provider: str = "simulation",
    parent_generation_id: str | None = None,
) -> CharacterJob:
    validation = validate_create_request(
        name=name,
        prompt=prompt,
        template_id=template_id,
        registry_slot=registry_slot,
        gender=gender,
        age=age,
        ethnicity=ethnicity,
        body_type=body_type,
        hairstyle=hairstyle,
        beard=beard,
        skin=skin,
        eye_color=eye_color,
        clothing=clothing,
        accessories=accessories,
    )
    if not validation.ok:
        raise ValueError("; ".join(validation.errors))

    t0 = time.perf_counter()
    tmpl = get_template(validation.template_id)
    seed = f"{validation.name or tmpl.name}|{prompt or ''}|{tmpl.template_id}"
    character_id = _character_id(seed)
    unique_id = _unique_id(seed)
    job_id = _job_id(character_id, unique_id)

    identity = build_identity(
        unique_id=unique_id,
        overrides=validation.overrides,
        template_id=tmpl.template_id,
    )
    dna = build_dna(character_id, identity, version=1)
    display_name = validation.name or tmpl.name
    record = CharacterRecord(
        character_id=character_id,
        registry_slot=validation.registry_slot,  # type: ignore[arg-type]
        identity=identity,
        dna=dna,
        metadata=CharacterMetadata(
            name=display_name,
            description=prompt or tmpl.description,
            tags=[tmpl.template_id, identity.gender, identity.ethnicity],
            template_id=tmpl.template_id,
            registry_slot=validation.registry_slot,
            source_prompt=prompt,
        ),
        character_version=1,
        production_ready=True,
        preview_url=f"/media/avatar/{character_id}/preview.png",
        dna_url=f"/media/avatar/{character_id}/character_dna.json",
    )
    record = registry.register(record, slot=validation.registry_slot)  # type: ignore[arg-type]

    paddle = paddle_status()
    processing_ms = round((time.perf_counter() - t0) * 1000.0, 3)
    job = CharacterJob(
        job_id=job_id,
        engine=ENGINE_NAME,
        version=ENGINE_VERSION,
        state="completed",
        character=record,
        processing_time_ms=processing_ms,
        provider=PROVIDER_SIMULATION if provider == "simulation" else provider,
        parent_generation_id=parent_generation_id,
        paddle_verified=bool(paddle.get("configured")),
        history=[
            {"status": "queued", "ts": time.time()},
            {"status": "preparing", "ts": time.time()},
            {"status": "generating", "ts": time.time()},
            {"status": "registering", "ts": time.time()},
            {"status": "completed", "ts": time.time()},
        ],
        metadata={
            "template_id": tmpl.template_id,
            "dna_fingerprint": dna.fingerprint,
            "paddle": {
                "configured": paddle.get("configured"),
                "message": paddle.get("message"),
                "secrets_exposed": False,
            },
            "provider_secret_exposed": False,
        },
    )
    store.save(job)
    return job


def get_character(character_id: str) -> CharacterRecord | None:
    return registry.get(character_id)


def get_job(job_id: str) -> CharacterJob | None:
    return store.get(job_id)


def list_characters(*, limit: int = 50) -> dict[str, Any]:
    registered = registry.list_registered()
    all_chars = registry.list_all()
    return {
        "registry": registry.registry_payload(),
        "characters": [c.to_dict() for c in all_chars[: max(1, min(500, limit))]],
        "count": len(all_chars),
        "slots_filled": len(registered),
        "templates": [t.to_dict() for t in list_templates()],
        "engine": ENGINE_LABEL,
        "paddle": paddle_status(),
    }


def create_character_dict(**kwargs: Any) -> dict[str, Any]:
    return create_character(**kwargs).to_dict()


def get_avatar_payload(character_or_job_id: str) -> dict[str, Any] | None:
    """Resolve by character_id or job_id."""
    record = registry.get(character_or_job_id)
    if record:
        return {"ok": True, **record.to_dict()}
    job = store.get(character_or_job_id)
    if job:
        return {"ok": True, **job.to_dict()}
    # Also try registry slots
    if character_or_job_id in ("Character_A", "Character_B", "Character_C"):
        slot_rec = registry.get_slot(character_or_job_id)  # type: ignore[arg-type]
        if slot_rec:
            return {"ok": True, **slot_rec.to_dict()}
    return None

"""Character reference loading — uploaded / generated / stored."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.face_lock.models import CharacterReference, ReferenceKind


def build_reference(
    character_id: str,
    *,
    kind: ReferenceKind = "stored",
    url: str | None = None,
    source: str | None = None,
) -> CharacterReference | None:
    resolved = (url or "").strip()
    if not resolved:
        if kind == "stored":
            resolved = f"/media/avatar/{character_id}/reference.png"
        elif kind == "generated":
            resolved = f"/media/avatar/{character_id}/generated_ref.png"
        else:
            return None
    ref_id = f"ref_{hashlib.sha1(f'{character_id}|{kind}|{resolved}'.encode()).hexdigest()[:12]}"
    return CharacterReference(
        reference_id=ref_id,
        kind=kind,
        url=resolved,
        character_id=character_id,
        source=source or kind,
    )


def resolve_reference_kind(kind: str | None) -> ReferenceKind:
    k = (kind or "stored").strip().lower()
    if k in ("uploaded", "upload", "user"):
        return "uploaded"
    if k in ("generated", "generate", "ai"):
        return "generated"
    return "stored"


def load_reference_payload(ref: CharacterReference) -> dict[str, Any]:
    return {
        "loaded": True,
        "reference": ref.to_dict(),
        "usable_for_lock": bool(ref.url),
    }

"""Persistent face embeddings — never regenerate unless explicitly requested."""

from __future__ import annotations

import hashlib
import math
import struct
from typing import Sequence

from app.services.face_lock.models import FaceEmbeddingRecord

EMBEDDING_DIM = 64


def _bytes_to_unit_vector(data: bytes, dim: int = EMBEDDING_DIM) -> list[float]:
    digest = hashlib.sha256(data).digest()
    buf = bytearray(digest)
    while len(buf) < dim * 4:
        buf.extend(hashlib.sha256(bytes(buf)).digest())
    values: list[float] = []
    for i in range(dim):
        chunk = bytes(buf[i * 4 : i * 4 + 4])
        (raw,) = struct.unpack(">I", chunk)
        values.append((raw / 0xFFFFFFFF) * 2.0 - 1.0)
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


def build_face_embedding(
    *,
    character_id: str,
    features_fingerprint: str,
    reference_url: str | None = None,
    regenerate: bool = False,
    existing: FaceEmbeddingRecord | None = None,
) -> FaceEmbeddingRecord:
    """Return existing embedding unless regenerate=True."""
    if existing and not regenerate:
        return FaceEmbeddingRecord(
            face_embedding_ref=existing.face_embedding_ref,
            dimension=existing.dimension,
            vector=list(existing.vector),
            regenerated=False,
            locked=True,
        )

    refs = [reference_url] if reference_url else []
    seed = "|".join([character_id, features_fingerprint, *refs, "v1"])
    vector = _bytes_to_unit_vector(seed.encode("utf-8"))
    if refs:
        ref = f"embedding://face/{hashlib.sha1(refs[0].encode()).hexdigest()[:16]}"
    else:
        ref = f"embedding://traits/{hashlib.sha1(seed.encode()).hexdigest()[:16]}"
    return FaceEmbeddingRecord(
        face_embedding_ref=ref,
        dimension=EMBEDDING_DIM,
        vector=vector,
        regenerated=bool(regenerate and existing),
        locked=True,
    )


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return max(-1.0, min(1.0, dot / (na * nb)))

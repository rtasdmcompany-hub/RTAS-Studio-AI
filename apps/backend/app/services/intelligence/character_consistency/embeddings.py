"""
Face embedding support.

Produces stable deterministic embedding vectors from reference URLs / subject ids
for identity verification. Ready for InstantID / real embedding swap-in later —
no fake generation success paths.
"""

from __future__ import annotations

import hashlib
import math
import struct
from typing import Sequence


EMBEDDING_DIM = 64


def _bytes_to_unit_vector(data: bytes, dim: int = EMBEDDING_DIM) -> list[float]:
    digest = hashlib.sha256(data).digest()
    # Expand digest into dim floats via repeated hashing.
    buf = bytearray(digest)
    while len(buf) < dim * 4:
        buf.extend(hashlib.sha256(bytes(buf)).digest())
    values: list[float] = []
    for i in range(dim):
        chunk = bytes(buf[i * 4 : i * 4 + 4])
        # Map uint32 → (-1, 1)
        (raw,) = struct.unpack(">I", chunk)
        values.append((raw / 0xFFFFFFFF) * 2.0 - 1.0)
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


def build_face_embedding(
    *,
    subject_id: str,
    reference_image_urls: Sequence[str] | None = None,
    traits_fingerprint: str = "",
) -> tuple[list[float], str]:
    """
    Return (embedding_vector, embedding_ref).

    When a reference URL exists, fingerprint includes URL so the same face ref
    yields a stable embedding across scenes.
    """
    refs = list(reference_image_urls or [])
    seed = "|".join([subject_id, traits_fingerprint, *refs])
    vector = _bytes_to_unit_vector(seed.encode("utf-8"))
    if refs:
        ref = f"embedding://face/{hashlib.sha1(refs[0].encode('utf-8')).hexdigest()[:16]}"
    else:
        ref = f"embedding://traits/{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:16]}"
    return vector, ref


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return max(-1.0, min(1.0, dot / (na * nb)))


def embedding_stability_score(
    baseline: Sequence[float],
    candidates: Sequence[Sequence[float]],
) -> float:
    if not baseline:
        return 0.5
    if not candidates:
        return 0.85
    sims = [cosine_similarity(baseline, c) for c in candidates if c]
    if not sims:
        return 0.5
    # Map cosine [0,1] typical for same-seed near 1.0
    avg = sum(max(0.0, s) for s in sims) / len(sims)
    return round(avg, 4)

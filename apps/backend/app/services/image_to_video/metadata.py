"""Extract and store image metadata for I2V planning."""

from __future__ import annotations

from typing import Any

from app.services.image_to_video.models import ImageAsset, ImageMetadataRecord, ImageRole


_ROLE_ALIASES: dict[str, ImageRole] = {
    "single": "single",
    "image": "single",
    "source": "single",
    "sourceimage": "single",
    "multiple": "multiple",
    "multi": "multiple",
    "sequence": "multiple",
    "reference": "reference",
    "referenceimage": "reference",
    "imagereference": "reference",
    "character": "character",
    "facereference": "character",
    "face": "character",
    "identity": "character",
    "product": "product",
    "productimage": "product",
    "logo": "logo",
    "coverimage": "reference",
}


def normalize_role(value: str | None, *, fallback: ImageRole = "reference") -> ImageRole:
    key = (value or "").strip().lower().replace("_", "").replace("-", "")
    return _ROLE_ALIASES.get(key, fallback)


def infer_aspect(width: int | None, height: int | None) -> str:
    if not width or not height or height <= 0:
        return "landscape"
    ratio = width / height
    if ratio < 0.85:
        return "vertical"
    if ratio > 1.15:
        return "landscape"
    return "square"


def build_image_metadata(
    images: list[ImageAsset],
    *,
    preserve_identity: bool = True,
    preserve_lighting: bool = True,
    preserve_composition: bool = True,
    preserve_environment: bool = True,
) -> list[ImageMetadataRecord]:
    preserve = {
        "identity": preserve_identity,
        "lighting": preserve_lighting,
        "composition": preserve_composition,
        "environment": preserve_environment,
    }
    records: list[ImageMetadataRecord] = []
    for img in images:
        records.append(
            ImageMetadataRecord(
                image_id=img.image_id,
                role=img.role,
                uri=img.resolved_uri,
                label=img.label or img.role,
                aspect_hint=infer_aspect(img.width, img.height),
                preserve=dict(preserve),
                extras={
                    "mime_type": img.mime_type,
                    "source_field": img.source_field,
                    "width": img.width,
                    "height": img.height,
                    **(img.metadata or {}),
                },
            )
        )
    return records


def ingest_image_inputs(
    images: list[dict[str, Any]] | None = None,
    *,
    single_image: str | None = None,
    multiple_images: list[str] | None = None,
    reference_images: list[str] | None = None,
    character_reference: str | None = None,
    product_reference: str | None = None,
    logo_reference: str | None = None,
) -> list[ImageAsset]:
    """Normalize heterogeneous image inputs into ImageAsset list."""
    out: list[ImageAsset] = []
    idx = 0

    def add(role: ImageRole, uri: str, *, field: str = "", label: str = "") -> None:
        nonlocal idx
        uri = (uri or "").strip()
        if not uri:
            return
        idx += 1
        is_url = uri.startswith(("http://", "https://", "data:"))
        out.append(
            ImageAsset(
                image_id=f"img_{idx}_{role}",
                role=role,
                url=uri if is_url else None,
                local_path=None if is_url else uri,
                label=label or role,
                source_field=field,
            )
        )

    for raw in images or []:
        if not isinstance(raw, dict):
            continue
        role = normalize_role(str(raw.get("role") or "reference"))
        uri = str(raw.get("url") or raw.get("local_path") or raw.get("uri") or "")
        add(
            role,
            uri,
            field=str(raw.get("source_field") or raw.get("field") or ""),
            label=str(raw.get("label") or ""),
        )
        if out:
            last = out[-1]
            if raw.get("mime_type"):
                last.mime_type = str(raw["mime_type"])
            if raw.get("width"):
                last.width = int(raw["width"])
            if raw.get("height"):
                last.height = int(raw["height"])
            if isinstance(raw.get("metadata"), dict):
                last.metadata.update(raw["metadata"])

    if single_image:
        add("single", single_image, field="singleImage", label="primary")
    for i, u in enumerate(multiple_images or []):
        add("multiple", u, field="multipleImages", label=f"frame_{i + 1}")
    for i, u in enumerate(reference_images or []):
        add("reference", u, field="referenceImages", label=f"ref_{i + 1}")
    if character_reference:
        add("character", character_reference, field="faceReference", label="character")
    if product_reference:
        add("product", product_reference, field="productImage", label="product")
    if logo_reference:
        add("logo", logo_reference, field="logoReference", label="logo")

    return out

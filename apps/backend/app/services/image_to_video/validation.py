"""Image validation for Image-to-Video Engine."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from app.services.image_to_video.models import (
    ImageAsset,
    ImageValidationIssue,
    ImageValidationResult,
)

_ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
_ALLOWED_MIME = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/bmp",
}


def _has_uri(image: ImageAsset) -> bool:
    return bool(image.resolved_uri)


def _looks_like_url(uri: str) -> bool:
    parsed = urlparse(uri)
    return parsed.scheme in ("http", "https", "data") and bool(parsed.netloc or parsed.path)


def _extension_ok(uri: str, mime: str | None) -> bool:
    if mime and mime.lower() in _ALLOWED_MIME:
        return True
    path = uri.split("?")[0].lower()
    return any(path.endswith(ext) for ext in _ALLOWED_EXT) or _looks_like_url(uri)


def validate_images(
    images: list[ImageAsset],
    *,
    require_character_for_identity: bool = False,
) -> ImageValidationResult:
    issues: list[ImageValidationIssue] = []
    checks: dict[str, bool] = {}

    checks["has_images"] = bool(images)
    if not images:
        issues.append(
            ImageValidationIssue(
                "missing_images",
                "error",
                "At least one image is required for image-to-video",
            )
        )

    uri_ok = True
    format_ok = True
    for img in images:
        if not _has_uri(img):
            uri_ok = False
            issues.append(
                ImageValidationIssue(
                    "missing_uri",
                    "error",
                    f"Image {img.image_id} has no url or local_path",
                    image_id=img.image_id,
                )
            )
            continue
        uri = img.resolved_uri
        if uri.startswith(("http://", "https://", "data:")):
            pass
        else:
            p = Path(uri)
            if not p.exists():
                # Allow planning with remote-like paths that aren't on disk yet
                issues.append(
                    ImageValidationIssue(
                        "local_missing",
                        "warning",
                        f"Local image path not found (may resolve at generate time): {uri}",
                        image_id=img.image_id,
                    )
                )
        if not _extension_ok(uri, img.mime_type):
            format_ok = False
            issues.append(
                ImageValidationIssue(
                    "unsupported_format",
                    "warning",
                    f"Unsupported or unknown image format for {img.image_id}",
                    image_id=img.image_id,
                )
            )

    checks["uris_present"] = uri_ok
    checks["formats_ok"] = format_ok

    roles = {i.role for i in images}
    checks["has_driving_image"] = bool(
        roles & {"single", "multiple", "character", "product"}
        or any(i.role == "reference" for i in images)
    )
    if images and not checks["has_driving_image"] and "logo" in roles and len(roles) == 1:
        issues.append(
            ImageValidationIssue(
                "logo_only",
                "warning",
                "Only logo reference provided — pair with product or character for best results",
            )
        )
        checks["has_driving_image"] = True  # still allow logo-driven motion

    multi = [i for i in images if i.role == "multiple"]
    checks["multi_coherent"] = len(multi) != 1  # 0 or >=2 is fine; single "multiple" is odd
    if len(multi) == 1:
        issues.append(
            ImageValidationIssue(
                "single_multiple_role",
                "info",
                "Only one image tagged as multiple — treat as sequence frame 1",
                image_id=multi[0].image_id,
            )
        )

    if require_character_for_identity:
        checks["has_character_ref"] = any(i.role == "character" for i in images)
        if not checks["has_character_ref"]:
            issues.append(
                ImageValidationIssue(
                    "missing_character",
                    "warning",
                    "Identity preservation requested but no character reference image",
                )
            )
    else:
        checks["has_character_ref"] = any(i.role == "character" for i in images)

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    passed = len(errors) == 0 and checks.get("has_images", False)
    score = 1.0 - 0.2 * len(errors) - 0.05 * len(warnings)
    score = max(0.0, min(1.0, round(score, 3)))

    return ImageValidationResult(
        passed=passed,
        score=score,
        issues=issues,
        checks=checks,
    )

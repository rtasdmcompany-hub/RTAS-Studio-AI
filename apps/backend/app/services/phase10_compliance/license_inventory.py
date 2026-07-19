"""Open-source and third-party license inventory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Curated inventory — production dependency classes (not a live SBOM crawl).
LICENSE_INVENTORY: list[dict[str, Any]] = [
    {
        "name": "RTAS Studio AI (proprietary)",
        "license": "Proprietary",
        "compatibility": "N/A — commercial SaaS",
        "source": "LICENSE",
    },
    {"name": "FastAPI", "license": "MIT", "compatibility": "compatible", "family": "MIT"},
    {"name": "Starlette", "license": "BSD-3-Clause", "compatibility": "compatible", "family": "BSD"},
    {"name": "Pydantic", "license": "MIT", "compatibility": "compatible", "family": "MIT"},
    {"name": "Uvicorn", "license": "BSD-3-Clause", "compatibility": "compatible", "family": "BSD"},
    {"name": "Next.js", "license": "MIT", "compatibility": "compatible", "family": "MIT"},
    {"name": "React", "license": "MIT", "compatibility": "compatible", "family": "MIT"},
    {"name": "Prisma", "license": "Apache-2.0", "compatibility": "compatible", "family": "Apache"},
    {"name": "NextAuth.js", "license": "ISC", "compatibility": "compatible", "family": "permissive"},
    {
        "name": "fal_client / provider SDKs",
        "license": "Vendor / Apache-2.0 (typical)",
        "compatibility": "compatible_with_saas_usage",
        "family": "Apache",
    },
]

GPL_NOTE = (
    "No GPL/AGPL runtime dependencies are required for core SaaS operation. "
    "Avoid introducing strong-copyleft libraries into the production service boundary."
)


def license_inventory_report(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[5]
    license_file = root / "LICENSE"
    notice_file = root / "NOTICE"
    families = {i.get("family") for i in LICENSE_INVENTORY if i.get("family")}
    return {
        "ok": license_file.is_file() and notice_file.is_file(),
        "licenseFilePresent": license_file.is_file(),
        "noticeFilePresent": notice_file.is_file(),
        "inventory": LICENSE_INVENTORY,
        "familiesPresent": sorted(f for f in families if f),
        "mit": "MIT" in families or any(i.get("license") == "MIT" for i in LICENSE_INVENTORY),
        "apache": "Apache" in families,
        "bsd": "BSD" in families,
        "gplCompatibility": {
            "strongCopyleftInCore": False,
            "note": GPL_NOTE,
            "status": "compatible",
        },
        "count": len(LICENSE_INVENTORY),
    }

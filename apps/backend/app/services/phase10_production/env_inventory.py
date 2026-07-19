"""Environment variable inventory — classify required/optional/missing/deprecated/unused.

Does NOT read or modify .env files on disk; inspects process environment + catalogs only.
"""

from __future__ import annotations

import os
from typing import Any, Literal

Classification = Literal["required", "optional", "missing", "deprecated", "unused"]

# (key, classification_if_absent_or_present_hint, surface)
# required = needed for full production; optional = feature-gated; deprecated = legacy alias
ENV_CATALOG: tuple[tuple[str, str, str], ...] = (
    # Next.js / web (documented; may not be in FastAPI process)
    ("DATABASE_URL", "required", "prisma"),
    ("NEXTAUTH_SECRET", "required", "nextjs"),
    ("NEXTAUTH_URL", "required", "nextjs"),
    ("GOOGLE_CLIENT_ID", "optional", "nextjs"),
    ("GOOGLE_CLIENT_SECRET", "optional", "nextjs"),
    # FastAPI
    ("AI_BACKEND_SECRET", "required", "fastapi"),
    ("CORS_ORIGINS", "required", "fastapi"),
    ("PUBLIC_BASE_URL", "optional", "fastapi"),
    ("AI_PROVIDER_MODE", "optional", "fastapi"),
    # Vercel
    ("VERCEL", "optional", "vercel"),
    ("VERCEL_URL", "optional", "vercel"),
    ("VERCEL_TOKEN", "optional", "vercel"),
    # Supabase
    ("SUPABASE_URL", "optional", "supabase"),
    ("SUPABASE_ANON_KEY", "optional", "supabase"),
    ("SUPABASE_SERVICE_ROLE_KEY", "optional", "supabase"),
    ("NEXT_PUBLIC_SUPABASE_URL", "optional", "supabase"),
    # Redis / Upstash
    ("UPSTASH_REDIS_REST_URL", "optional", "redis"),
    ("UPSTASH_REDIS_REST_TOKEN", "optional", "redis"),
    ("KV_REST_API_URL", "optional", "redis"),
    ("KV_REST_API_TOKEN", "optional", "redis"),
    ("REDIS_URL", "optional", "redis"),
    # Storage
    ("STORAGE_MODE", "optional", "storage"),
    ("BLOB_READ_WRITE_TOKEN", "optional", "storage"),
    ("S3_BUCKET", "optional", "storage"),
    # AI
    ("FAL_KEY", "optional", "ai_providers"),
    ("FAL_API_KEY", "optional", "ai_providers"),
    ("REPLICATE_API_TOKEN", "optional", "ai_providers"),
    ("OPENAI_API_KEY", "optional", "ai_providers"),
    ("ANTHROPIC_API_KEY", "optional", "ai_providers"),
    ("CLAUDE_API_KEY", "deprecated", "ai_providers"),
    ("GEMINI_API_KEY", "optional", "ai_providers"),
    ("GOOGLE_API_KEY", "optional", "ai_providers"),
    ("RUNPOD_API_KEY", "optional", "ai_providers"),
    ("RUNPOD_API_KEY_V2", "optional", "ai_providers"),
    ("COMFYUI_API_URL", "optional", "ai_providers"),
    # Billing
    ("PADDLE_API_KEY", "optional", "billing"),
    ("PADDLE_WEBHOOK_SECRET", "optional", "billing"),
    ("PAYPAL_CLIENT_ID", "optional", "billing"),
    ("PAYPAL_CLIENT_SECRET", "optional", "billing"),
    ("PAYPAL_SECRET", "deprecated", "billing"),
    # Email / ops
    ("RESEND_API_KEY", "optional", "email"),
    ("GITHUB_TOKEN", "optional", "github"),
    # Marketplace / developer (no dedicated secrets — platform flags)
    ("RTAS_JWT_SECRET", "optional", "security"),
    ("RTAS_GENERATION_WEBHOOK_SECRET", "optional", "security"),
)

# Keys that are legacy aliases — present is OK, prefer primary
DEPRECATED_KEYS = frozenset({"CLAUDE_API_KEY", "PAYPAL_SECRET", "FAL_API_KEY"})

# Documented but intentionally unused in FastAPI process
UNUSED_IN_BACKEND = frozenset(
    {
        "NEXTAUTH_SECRET",
        "NEXTAUTH_URL",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "NEXT_PUBLIC_SUPABASE_URL",
        "GITHUB_TOKEN",
        "RESEND_API_KEY",
    }
)


def _present(key: str) -> bool:
    val = os.environ.get(key)
    return bool(val and str(val).strip())


def build_environment_inventory() -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    by_class: dict[str, list[str]] = {
        "required": [],
        "optional": [],
        "missing": [],
        "deprecated": [],
        "unused": [],
    }

    for key, intended, surface in ENV_CATALOG:
        is_set = _present(key)
        if key in DEPRECATED_KEYS:
            classification: Classification = "deprecated" if is_set else "optional"
            if is_set:
                by_class["deprecated"].append(key)
            else:
                by_class["optional"].append(key)
        elif key in UNUSED_IN_BACKEND and not is_set:
            classification = "unused"
            by_class["unused"].append(key)
        elif intended == "required" and not is_set:
            classification = "missing"
            by_class["missing"].append(key)
            by_class["required"].append(key)
        elif intended == "required" and is_set:
            classification = "required"
            by_class["required"].append(key)
        elif is_set:
            classification = "optional"
            by_class["optional"].append(key)
        else:
            classification = "optional"
            by_class["optional"].append(key)
            if key in UNUSED_IN_BACKEND:
                classification = "unused"
                by_class["unused"].append(key)

        items.append(
            {
                "key": key,
                "present": is_set,
                "classification": classification,
                "intended": intended,
                "surface": surface,
                # Never expose secret values
                "valueExposed": False,
            }
        )

    # Required missing among production-critical for THIS process
    critical_missing = [
        i["key"]
        for i in items
        if i["intended"] == "required"
        and not i["present"]
        and i["surface"] in ("fastapi", "prisma", "security")
    ]

    return {
        "ok": True,
        "inspectedProcessEnvOnly": True,
        "envFilesModified": False,
        "count": len(items),
        "items": items,
        "byClassification": {k: sorted(set(v)) for k, v in by_class.items()},
        "criticalMissingInProcess": critical_missing,
        "note": "Inventory does not modify .env files; web-only vars may be unused in FastAPI process",
    }

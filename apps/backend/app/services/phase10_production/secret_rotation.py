"""Secret rotation plan — checklist only. NEVER rotates or mutates secrets."""

from __future__ import annotations

from typing import Any

ROTATION_TARGETS: tuple[dict[str, Any], ...] = (
    {
        "provider": "openai",
        "keys": ["OPENAI_API_KEY"],
        "procedure": "Create new key in OpenAI dashboard → set in Vercel → verify → revoke old",
    },
    {
        "provider": "anthropic",
        "keys": ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"],
        "procedure": "Rotate Anthropic key → update env → smoke AI route → revoke old",
    },
    {
        "provider": "google_gemini",
        "keys": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "procedure": "Rotate Google AI Studio / Cloud key → update env → verify",
    },
    {
        "provider": "fal_ai",
        "keys": ["FAL_KEY", "FAL_API_KEY"],
        "procedure": "Rotate fal.ai key on API + Web → verify /api/ready fal → revoke old",
    },
    {
        "provider": "runpod",
        "keys": ["RUNPOD_API_KEY", "RUNPOD_API_KEY_V2"],
        "procedure": "Rotate RunPod API key → update worker env → verify ComfyURL",
    },
    {
        "provider": "paddle",
        "keys": ["PADDLE_API_KEY", "PADDLE_WEBHOOK_SECRET"],
        "procedure": "Rotate Paddle API + webhook secret → update web + API → replay test webhook",
    },
    {
        "provider": "paypal",
        "keys": ["PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET", "PAYPAL_SECRET"],
        "procedure": "Rotate PayPal REST credentials → update env → verify wallet routes",
    },
    {
        "provider": "supabase",
        "keys": ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"],
        "procedure": "Rotate service role carefully → update Prisma/Supabase clients → verify auth",
    },
    {
        "provider": "vercel",
        "keys": ["VERCEL_TOKEN"],
        "procedure": "Rotate Vercel token used by CI → update GitHub secrets → redeploy",
    },
    {
        "provider": "upstash",
        "keys": ["UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN", "KV_REST_API_TOKEN"],
        "procedure": "Rotate Upstash REST token → update web + API → verify KV writes",
    },
    {
        "provider": "resend",
        "keys": ["RESEND_API_KEY"],
        "procedure": "Rotate Resend API key → update web mailer → send test email",
    },
    {
        "provider": "github",
        "keys": ["GITHUB_TOKEN"],
        "procedure": "Rotate PAT / GitHub App token → update CI secrets → verify workflows",
    },
)


def secret_rotation_checklist() -> dict[str, Any]:
    items = []
    for target in ROTATION_TARGETS:
        items.append(
            {
                **target,
                "rotated": False,
                "readyToRotate": True,
                "secretsModified": False,
                "status": "plan_only",
            }
        )
    return {
        "ok": True,
        "rotatedAnySecret": False,
        "secretsModified": False,
        "checklist": items,
        "count": len(items),
        "policy": "DO NOT rotate secrets during Sprint 9 validation — plan readiness only",
    }

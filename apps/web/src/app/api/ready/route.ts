import { NextResponse } from "next/server";
import {
  getEmailDeliveryMode,
  isEmailDeliveryConfigured,
  isFalConfigured,
  isGoogleAuthConfigured,
  isReplicateConfigured,
  resolveServerFastApiUrl,
} from "@/lib/env";
import {
  getPersistentStoreMode,
  isPersistentStoreConfigured,
} from "@/lib/server/persistent-store";
import { getObservabilityStatus } from "@/lib/observability";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type CheckResult = {
  ok: boolean;
  detail?: string;
};

function hasEnv(key: string): boolean {
  const v = process.env[key]?.trim() ?? "";
  return v.length > 0;
}

/**
 * Readiness probe — required production dependencies.
 * Returns 200 when ready to serve traffic; 503 when critical deps missing.
 * Does not print secret values.
 * GET /api/ready
 */
export async function GET() {
  const isProd = process.env.NODE_ENV === "production";
  const fastApi = resolveServerFastApiUrl();
  const paymentProvider = (
    process.env.NEXT_PUBLIC_PAYMENT_PROVIDER || "paddle"
  ).toLowerCase();

  const checks: Record<string, CheckResult> = {
    nextAuthSecret: {
      ok:
        !isProd ||
        (hasEnv("NEXTAUTH_SECRET") &&
          !["change-me", "generate-with-openssl-rand-base64-32"].includes(
            process.env.NEXTAUTH_SECRET?.trim() || ""
          )),
      detail: isProd ? undefined : "skipped-in-non-production",
    },
    database: {
      ok: hasEnv("DATABASE_URL"),
      detail: hasEnv("DATABASE_URL") ? "configured" : "DATABASE_URL missing",
    },
    fastApi: {
      ok: fastApi.ok,
      detail: fastApi.ok
        ? "configured"
        : fastApi.error?.slice(0, 120) || "FASTAPI_URL missing",
    },
    persistentStore: {
      ok: !isProd || isPersistentStoreConfigured(),
      detail: isPersistentStoreConfigured()
        ? getPersistentStoreMode()
        : isProd
          ? "KV/Redis required on Vercel"
          : "optional-locally",
    },
    email: {
      ok: !isProd || isEmailDeliveryConfigured(),
      detail: isEmailDeliveryConfigured()
        ? getEmailDeliveryMode()
        : "RESEND_API_KEY or SMTP_* missing",
    },
    aiProvider: {
      ok: !isProd || isFalConfigured() || isReplicateConfigured(),
      detail:
        isFalConfigured() || isReplicateConfigured()
          ? "cloud-ai-configured"
          : "FAL_KEY or REPLICATE_API_TOKEN recommended",
    },
    payments: {
      ok:
        paymentProvider !== "paddle" ||
        !isProd ||
        hasEnv("PADDLE_WEBHOOK_SECRET"),
      detail:
        paymentProvider === "paddle"
          ? hasEnv("PADDLE_WEBHOOK_SECRET")
            ? "paddle-webhook-configured"
            : "PADDLE_WEBHOOK_SECRET missing"
          : paymentProvider,
    },
    googleOAuth: {
      ok: true,
      detail: isGoogleAuthConfigured() ? "configured" : "optional",
    },
  };

  const criticalKeys = [
    "nextAuthSecret",
    "database",
    "fastApi",
    "persistentStore",
    "payments",
  ] as const;

  const ready = criticalKeys.every((k) => checks[k].ok);
  const observability = getObservabilityStatus();

  return NextResponse.json(
    {
      status: ready ? "ready" : "not_ready",
      service: "rtas-web",
      timestamp: new Date().toISOString(),
      environment: process.env.NODE_ENV || "development",
      paymentProvider,
      checks,
      observability,
    },
    {
      status: ready ? 200 : 503,
      headers: {
        "Cache-Control": "no-store, max-age=0",
      },
    }
  );
}

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

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

function hasEnv(key: string): boolean {
  const v = process.env[key]?.trim() ?? "";
  return v.length > 0;
}

/**
 * Public subsystem summary for /status — no secrets, no connection strings.
 * GET /api/status/summary
 */
export async function GET() {
  const isProd = process.env.NODE_ENV === "production";
  const fastApi = resolveServerFastApiUrl();
  const paymentProvider = (
    process.env.NEXT_PUBLIC_PAYMENT_PROVIDER || "paddle"
  ).toLowerCase();
  const deferPaddle =
    process.env.RTAS_DEFER_PADDLE === "1" ||
    process.env.RTAS_DEFER_PADDLE === "true";

  const databaseOk = hasEnv("DATABASE_URL");
  const storageOk = !isProd || isPersistentStoreConfigured();
  const emailOk = !isProd || isEmailDeliveryConfigured();
  const gpuOk = fastApi.ok || isFalConfigured() || isReplicateConfigured();
  const billingOk =
    paymentProvider !== "paddle" ||
    !isProd ||
    hasEnv("PADDLE_WEBHOOK_SECRET") ||
    deferPaddle;

  const label = (ok: boolean, whenOk: string, whenNot: string) =>
    ok ? whenOk : whenNot;

  return NextResponse.json(
    {
      web: "operational",
      api: label(fastApi.ok, "configured", "not_configured_or_unreachable"),
      gpu: label(
        gpuOk,
        fastApi.ok
          ? "worker_endpoint_configured"
          : "cloud_ai_configured",
        "placeholder_no_gpu_probe"
      ),
      database: label(databaseOk, "configured", "not_configured"),
      storage: label(
        storageOk,
        isPersistentStoreConfigured()
          ? getPersistentStoreMode()
          : "optional_local",
        "not_configured"
      ),
      email: label(
        emailOk,
        isEmailDeliveryConfigured() ? getEmailDeliveryMode() : "dev_optional",
        "not_configured"
      ),
      auth: label(
        !isProd || hasEnv("NEXTAUTH_SECRET"),
        isGoogleAuthConfigured() ? "sessions_oauth_ready" : "sessions_ready",
        "secret_missing"
      ),
      billing: label(
        billingOk,
        deferPaddle && !hasEnv("PADDLE_WEBHOOK_SECRET")
          ? "paddle_deferred"
          : `${paymentProvider}_ready`,
        "webhook_not_configured"
      ),
      timestamp: new Date().toISOString(),
      note: "Public labels only — detailed dependency checks require admin readiness probe.",
    },
    {
      status: 200,
      headers: { "Cache-Control": "no-store, max-age=0" },
    }
  );
}

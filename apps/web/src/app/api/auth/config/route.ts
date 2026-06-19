import { NextResponse } from "next/server";
import { getPublicRuntimeConfig } from "@/lib/env";

type BackendHealth = {
  fal?: {
    configured?: boolean;
    valid?: boolean;
    live_generation?: boolean;
  };
  replicate?: {
    configured?: boolean;
    valid?: boolean;
    live_generation?: boolean;
  };
};

/** Public runtime flags for auth UI and client fallbacks (no secrets exposed). */
export async function GET() {
  const config = getPublicRuntimeConfig();

  try {
    const res = await fetch(`${config.fastApiUrl}/api/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(15000),
    });
    if (res.ok) {
      const health = (await res.json()) as BackendHealth;
      const falConfigured =
        Boolean(health.fal?.configured) || config.falConfigured;
      const replicateConfigured =
        Boolean(health.replicate?.configured) || config.replicateConfigured;
      const cloudConfigured = falConfigured || replicateConfigured;

      return NextResponse.json({
        ...config,
        falConfigured,
        replicateConfigured,
        simulationMode: !cloudConfigured,
      });
    }
  } catch {
    /* fall back to local env flags */
  }

  return NextResponse.json(config);
}

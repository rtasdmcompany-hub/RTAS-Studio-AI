type FalFundingResponse = {
  snapshot: {
    balanceUsd: number | null;
    requiredPoolUsd: number;
    activePremium: number;
    activeTester: number;
    shortfallUsd: number;
    checkedAt: string;
    topUpRecommendedUsd: number;
    alertMessage?: string;
  };
  ledger: {
    totalEntries: number;
    totalFalBudgetUsd: number;
    lastEntryAt?: string;
  };
  falBillingUrl: string;
  autoRechargeHint?: string;
};

function webAppUrl(): string {
  return (
    process.env.WEB_APP_URL?.replace(/\/$/, "") ||
    process.env.NEXT_PUBLIC_WEB_APP_URL?.replace(/\/$/, "") ||
    "http://localhost:3000"
  );
}

function adminSecret(): string | undefined {
  return process.env.RTAS_ADMIN_SECRET?.trim() || undefined;
}

export async function fetchAdminFundingSnapshot(): Promise<{
  data?: FalFundingResponse;
  error?: string;
}> {
  try {
    const headers: Record<string, string> = { Accept: "application/json" };
    const secret = adminSecret();
    if (secret) headers["x-rtas-admin-secret"] = secret;

    const res = await fetch(`${webAppUrl()}/api/admin/fal-funding`, {
      headers,
      cache: "no-store",
    });

    if (!res.ok) {
      const body = await res.text().catch(() => "");
      return {
        error: `Web admin API returned ${res.status}${body ? `: ${body.slice(0, 180)}` : ""}`,
      };
    }

    const data = (await res.json()) as FalFundingResponse;
    return { data };
  } catch (err) {
    return {
      error: err instanceof Error ? err.message : "Failed to reach web admin API",
    };
  }
}

export async function refreshAdminFundingSnapshot(): Promise<{
  ok: boolean;
  error?: string;
}> {
  try {
    const res = await fetch(`${webAppUrl()}/api/admin/fal-funding/refresh`, {
      method: "POST",
      cache: "no-store",
    });
    if (!res.ok) {
      return { ok: false, error: `Refresh failed (${res.status})` };
    }
    return { ok: true };
  } catch (err) {
    return {
      ok: false,
      error: err instanceof Error ? err.message : "Refresh request failed",
    };
  }
}

export async function resetBackendFalGuard(): Promise<{
  ok: boolean;
  error?: string;
}> {
  const base =
    process.env.FASTAPI_URL?.replace(/\/$/, "") ||
    process.env.NEXT_PUBLIC_FASTAPI_URL?.replace(/\/$/, "") ||
    "http://localhost:8000";
  const secret =
    process.env.AI_BACKEND_SECRET?.trim() ||
    process.env.RTAS_ADMIN_SECRET?.trim();

  try {
    const headers: Record<string, string> = { Accept: "application/json" };
    if (secret) headers["x-rtas-admin-secret"] = secret;

    const res = await fetch(`${base}/api/admin/fal/reset-guard`, {
      method: "POST",
      headers,
      cache: "no-store",
    });
    if (!res.ok) {
      return { ok: false, error: `Backend reset failed (${res.status})` };
    }
    return { ok: true };
  } catch (err) {
    return {
      ok: false,
      error: err instanceof Error ? err.message : "Backend reset request failed",
    };
  }
}

/** Read Fal.ai prepaid wallet balance (monitoring only — no programmatic top-up API). */

export type FalBalanceResult = {
  balanceUsd: number | null;
  currency: string;
  username: string | null;
  error?: string;
};

export async function fetchFalAccountBalance(): Promise<FalBalanceResult> {
  const key = process.env.FAL_ADMIN_API_KEY?.trim() || process.env.FAL_KEY?.trim();
  if (!key) {
    return {
      balanceUsd: null,
      currency: "USD",
      username: null,
      error: "FAL_KEY not configured on web server",
    };
  }

  try {
    const res = await fetch(
      "https://api.fal.ai/v1/account/billing?expand=credits",
      {
        headers: { Authorization: `Key ${key}` },
        cache: "no-store",
      }
    );

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      return {
        balanceUsd: null,
        currency: "USD",
        username: null,
        error: `Fal billing API ${res.status}: ${text.slice(0, 120)}`,
      };
    }

    const data = (await res.json()) as {
      username?: string;
      credits?: { current_balance?: number; currency?: string };
    };

    return {
      balanceUsd:
        typeof data.credits?.current_balance === "number"
          ? data.credits.current_balance
          : null,
      currency: data.credits?.currency ?? "USD",
      username: data.username ?? null,
    };
  } catch (e) {
    return {
      balanceUsd: null,
      currency: "USD",
      username: null,
      error: e instanceof Error ? e.message : "Fal balance check failed",
    };
  }
}

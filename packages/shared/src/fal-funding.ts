import { MONTHLY_CREDITS, TESTER_CREDITS } from "./credits";

/** ~$39 Fal budget per 2000 credits (1 credit = 1 second). Override via env on server. */
export const DEFAULT_FAL_USD_PER_CREDIT = 39 / MONTHLY_CREDITS;

export type PaidPlanType = "tester" | "standard" | "premium";

export function falBudgetUsdForCredits(
  credits: number,
  usdPerCredit: number = DEFAULT_FAL_USD_PER_CREDIT
): number {
  return Math.round(credits * usdPerCredit * 100) / 100;
}

export function falBudgetUsdForPlan(
  plan: PaidPlanType,
  usdPerCredit: number = DEFAULT_FAL_USD_PER_CREDIT
): number {
  const credits =
    plan === "tester"
      ? TESTER_CREDITS
      : MONTHLY_CREDITS;
  return falBudgetUsdForCredits(credits, usdPerCredit);
}

/** Reserve pool = sum of active customer Fal budgets + safety buffer */
export function requiredFalPoolUsd(
  activePremiumCount: number,
  activeTesterCount: number,
  usdPerCredit: number = DEFAULT_FAL_USD_PER_CREDIT,
  bufferPercent: number = 20
): number {
  const base =
    activePremiumCount * falBudgetUsdForPlan("premium", usdPerCredit) +
    activeTesterCount * falBudgetUsdForPlan("tester", usdPerCredit);
  return Math.round(base * (1 + bufferPercent / 100) * 100) / 100;
}

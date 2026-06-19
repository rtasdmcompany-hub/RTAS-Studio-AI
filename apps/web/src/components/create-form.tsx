"use client";

import type { VideoCategory, VisualStyle } from "@rtas/shared";

/** Mirrors backend model_routing.py — hard budget ceiling per second. */
export const HARD_BUDGET_CEILING_USD = 0.02;
/** Cheapest tier — weighted deduction stays 1:1 with seconds. */
export const CHEAP_FLOOR_USD = 0.005;
/** Max credit multiplier at the budget ceiling (5:1 vs floor). */
export const MAX_CREDIT_WEIGHT = 5;

export function creditWeightForCost(costPerSecond: number): number {
  const cost = Math.min(
    Math.max(costPerSecond, CHEAP_FLOOR_USD),
    HARD_BUDGET_CEILING_USD
  );
  if (cost <= CHEAP_FLOOR_USD) return 1;
  const span = HARD_BUDGET_CEILING_USD - CHEAP_FLOOR_USD;
  return 1 + ((cost - CHEAP_FLOOR_USD) / span) * (MAX_CREDIT_WEIGHT - 1);
}

export function weightedCreditsForDuration(
  durationSeconds: number,
  costPerSecond: number
): number {
  const weight = creditWeightForCost(costPerSecond);
  return Math.max(1, Math.round(durationSeconds * weight));
}

type CreateFormCostNoticeProps = {
  durationSeconds: number;
  category: VideoCategory;
  visualStyle: VisualStyle;
};

export function CreateFormCostNotice({
  durationSeconds,
  category,
  visualStyle,
}: CreateFormCostNoticeProps) {
  const seconds = Math.max(1, durationSeconds);
  const minCredits = weightedCreditsForDuration(seconds, CHEAP_FLOOR_USD);
  const maxCredits = weightedCreditsForDuration(seconds, HARD_BUDGET_CEILING_USD);

  return (
    <p className="create-form-cost-notice" role="note">
      Cost-optimized routing for {category} ({visualStyle}):{" "}
      <strong>
        {minCredits}–{maxCredits} credits
      </strong>{" "}
      for {seconds}s. Budget cap ${HARD_BUDGET_CEILING_USD.toFixed(3)}/s · weighted
      deduction 1:1 (cheap) to 5:1 (ceiling).
    </p>
  );
}

export function parseDurationSeconds(raw: string | undefined, fallback = 30): number {
  if (!raw?.trim()) return fallback;
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

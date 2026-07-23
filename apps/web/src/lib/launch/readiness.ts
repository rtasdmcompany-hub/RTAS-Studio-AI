/**
 * Phase 13 Sprint 9 — Executive launch readiness scores.
 * Computed from checklist status — never invent 100%s.
 */

import { LAUNCH_CHECKLIST } from "./checklist";
import type { LaunchChecklistItem, LaunchItemStatus, ReadinessDimension, ReadinessScore } from "./types";

const STATUS_WEIGHT: Record<LaunchItemStatus, number> = {
  done: 1,
  in_progress: 0.55,
  planned: 0.2,
  not_started: 0,
  blocked: 0.1,
};

const DIMENSION_META: Record<
  ReadinessDimension,
  { label: string; categories: LaunchChecklistItem["category"][] }
> = {
  infra: { label: "Infrastructure", categories: ["infra", "product"] },
  security: { label: "Security", categories: ["security"] },
  marketing: { label: "Marketing", categories: ["marketing"] },
  sales: { label: "Sales", categories: ["sales"] },
  support: { label: "Support", categories: ["support"] },
  business: { label: "Business", categories: ["business"] },
};

function scoreItems(items: LaunchChecklistItem[]): number {
  if (items.length === 0) return 0;
  const sum = items.reduce((acc, i) => acc + (STATUS_WEIGHT[i.status] ?? 0), 0);
  return Math.round((sum / items.length) * 100);
}

function notesFor(dimension: ReadinessDimension, items: LaunchChecklistItem[], score: number): string {
  const blocked = items.filter((i) => i.status === "blocked");
  if (blocked.length > 0) {
    return `Blocked: ${blocked.map((b) => b.title).join("; ")}.`;
  }
  if (score >= 85) return "Strong — remaining gaps are incremental.";
  if (score >= 60) return "Partial — active work or planned items remain.";
  return "Early — material checklist items incomplete.";
}

export function computeReadinessScores(
  items: LaunchChecklistItem[] = LAUNCH_CHECKLIST
): ReadinessScore[] {
  return (Object.keys(DIMENSION_META) as ReadinessDimension[]).map((dimension) => {
    const meta = DIMENSION_META[dimension];
    const subset = items.filter((i) => meta.categories.includes(i.category));
    const score = scoreItems(subset);
    return {
      dimension,
      score,
      max: 100,
      label: meta.label,
      notes: notesFor(dimension, subset, score),
    };
  });
}

export function computeOverallReadiness(scores: ReadinessScore[]): {
  score: number;
  label: string;
} {
  if (scores.length === 0) return { score: 0, label: "No data" };
  const score = Math.round(scores.reduce((a, s) => a + s.score, 0) / scores.length);
  let label = "Not ready";
  if (score >= 80) label = "Launch-capable with gaps";
  else if (score >= 65) label = "Ready with minor fixes";
  else if (score >= 45) label = "Partial readiness";
  return { score, label };
}

export function buildLaunchReadinessPayload() {
  const dimensions = computeReadinessScores();
  const overall = computeOverallReadiness(dimensions);
  return {
    dimensions,
    overall,
    integrityNote:
      "Scores derive from checklist item weights (done/in_progress/planned/blocked). They are not market share, revenue, or traffic claims.",
    generatedAt: new Date().toISOString(),
  };
}

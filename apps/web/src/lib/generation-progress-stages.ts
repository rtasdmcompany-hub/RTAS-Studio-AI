/**
 * Premium generation progress copy — display only.
 * Shared by pipeline panel, overlay, and progress simulation.
 */

export type GenerationProgressStage = {
  id: string;
  /** Live status message shown during this band */
  label: string;
  /** Compact checklist / chip label */
  shortLabel: string;
  min: number;
  max: number;
};

export const GENERATION_PROGRESS_STAGES: GenerationProgressStage[] = [
  {
    id: "upload",
    label: "Uploading Assets...",
    shortLabel: "Uploading Assets",
    min: 0,
    max: 12,
  },
  {
    id: "analyze",
    label: "Analyzing Prompt...",
    shortLabel: "Analyzing Prompt",
    min: 13,
    max: 25,
  },
  {
    id: "prepare",
    label: "Preparing AI Model...",
    shortLabel: "Preparing AI Model",
    min: 26,
    max: 38,
  },
  {
    id: "optimize",
    label: "Optimizing Settings...",
    shortLabel: "Optimizing Settings",
    min: 39,
    max: 48,
  },
  {
    id: "generate",
    label: "Generating...",
    shortLabel: "Generating",
    min: 49,
    max: 72,
  },
  {
    id: "render",
    label: "Rendering...",
    shortLabel: "Rendering",
    min: 73,
    max: 88,
  },
  {
    id: "finalize",
    label: "Finalizing...",
    shortLabel: "Finalizing",
    min: 89,
    max: 99,
  },
  {
    id: "done",
    label: "Done ✓",
    shortLabel: "Done",
    min: 100,
    max: 100,
  },
];

export const GENERATION_LAST_STAGE_INDEX = GENERATION_PROGRESS_STAGES.length - 1;

export function stageIndexFromPercent(percent: number): number {
  const p = Math.min(100, Math.max(0, percent));
  if (p >= 100) return GENERATION_LAST_STAGE_INDEX;
  for (let i = 0; i < GENERATION_PROGRESS_STAGES.length; i++) {
    const stage = GENERATION_PROGRESS_STAGES[i];
    if (p >= stage.min && p <= stage.max) return i;
  }
  return 0;
}

export function messageForPercent(percent: number): string {
  return GENERATION_PROGRESS_STAGES[stageIndexFromPercent(percent)].label;
}

export function isProgressStageDone(index: number, percent: number): boolean {
  const stage = GENERATION_PROGRESS_STAGES[index];
  if (!stage) return false;
  if (percent >= 100) return true;
  return percent > stage.max;
}

/** High-level rail (4 steps) mapped from percent — keeps the top stepper calm. */
export function pipelineRailIndexFromPercent(percent: number): number {
  if (percent < 13) return 0;
  if (percent < 49) return 1;
  if (percent < 89) return 2;
  return 3;
}

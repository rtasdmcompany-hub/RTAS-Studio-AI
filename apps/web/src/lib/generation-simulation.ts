import { CINEMATIC_SHOWCASE_VIDEO_URL } from "@/lib/preview-showcase";
import {
  GENERATION_LAST_STAGE_INDEX,
  GENERATION_PROGRESS_STAGES,
  messageForPercent,
  stageIndexFromPercent,
  type GenerationProgressStage,
} from "@/lib/generation-progress-stages";

export const PREVIEW_PLACEHOLDER_VIDEO = CINEMATIC_SHOWCASE_VIDEO_URL;

export type GenerationStage = GenerationProgressStage;

export const GENERATION_STAGES = GENERATION_PROGRESS_STAGES;

export type GenerationProgressCallback = (
  percent: number,
  message: string,
  stageIndex: number
) => void;

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** ~5–8s total; eased progress across premium stages */
export async function runGenerationSimulation(
  onProgress: GenerationProgressCallback,
  options?: { useInstantIdStep?: boolean; durationMs?: number }
): Promise<void> {
  const totalMs = options?.durationMs ?? 6500;
  const stageMs = totalMs / GENERATION_PROGRESS_STAGES.length;

  onProgress(0, GENERATION_PROGRESS_STAGES[0].label, 0);

  for (let i = 0; i < GENERATION_PROGRESS_STAGES.length; i++) {
    const stage = GENERATION_PROGRESS_STAGES[i];
    const steps = 10;
    const stepMs = stageMs / steps;

    for (let s = 0; s <= steps; s++) {
      const t = s / steps;
      const percent = Math.round(stage.min + t * (stage.max - stage.min));
      const clamped = Math.min(100, percent);
      onProgress(clamped, stage.label, i);
      if (clamped < 100) await delay(stepMs);
    }
  }

  onProgress(100, "Done ✓", GENERATION_LAST_STAGE_INDEX);
  await delay(400);
}

export function messageAtPercent(percent: number): string {
  return messageForPercent(percent);
}

export { stageIndexFromPercent };

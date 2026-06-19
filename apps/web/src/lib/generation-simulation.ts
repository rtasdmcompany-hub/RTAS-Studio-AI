import { CINEMATIC_SHOWCASE_VIDEO_URL } from "@/lib/preview-showcase";

export const PREVIEW_PLACEHOLDER_VIDEO = CINEMATIC_SHOWCASE_VIDEO_URL;

export interface GenerationStage {
  min: number;
  max: number;
  label: string;
}

export const GENERATION_STAGES: GenerationStage[] = [
  {
    min: 0,
    max: 20,
    label: "Initializing RTAS AI Engine & parsing assets…",
  },
  {
    min: 21,
    max: 50,
    label: "Syncing facial features via Instant-ID pipeline…",
  },
  {
    min: 51,
    max: 80,
    label: "Generating high-fidelity cinematic video frames…",
  },
  {
    min: 81,
    max: 100,
    label: "Finalizing video compilation and rendering preview…",
  },
];

export type GenerationProgressCallback = (
  percent: number,
  message: string,
  stageIndex: number
) => void;

function stageForPercent(percent: number): GenerationStage {
  for (const stage of GENERATION_STAGES) {
    if (percent >= stage.min && percent <= stage.max) return stage;
  }
  return GENERATION_STAGES[GENERATION_STAGES.length - 1];
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** ~5–8s total; 4 stages with eased progress */
export async function runGenerationSimulation(
  onProgress: GenerationProgressCallback,
  options?: { useInstantIdStep?: boolean; durationMs?: number }
): Promise<void> {
  const totalMs = options?.durationMs ?? 6500;
  const stageMs = totalMs / GENERATION_STAGES.length;
  const useInstantId = options?.useInstantIdStep !== false;

  onProgress(0, GENERATION_STAGES[0].label, 0);

  for (let i = 0; i < GENERATION_STAGES.length; i++) {
    const stage = GENERATION_STAGES[i];
    const label =
      i === 1 && !useInstantId
        ? "Applying style embeddings & scene composition…"
        : stage.label;

    const steps = 12;
    const stepMs = stageMs / steps;

    for (let s = 0; s <= steps; s++) {
      const t = s / steps;
      const percent = Math.round(stage.min + t * (stage.max - stage.min));
      const clamped = Math.min(100, percent);
      onProgress(clamped, label, i);
      if (clamped < 100) await delay(stepMs);
    }
  }

  onProgress(100, "Complete — loading preview…", GENERATION_STAGES.length - 1);
  await delay(400);
}

export function messageAtPercent(percent: number): string {
  return stageForPercent(percent).label;
}

/**
 * Local mock generation when the GPU worker / FastAPI is unavailable.
 * Keeps the Studio UX complete: progress → preview → download path (preview license).
 */

import { randomUUID } from "crypto";
import { GENERATION_PROGRESS_STAGES } from "@/lib/generation-progress-stages";
import { PRIMARY_SHOWCASE_STREAM_URL } from "@/lib/preview-showcase";

export type MockGenerationInput = {
  durationSeconds: number;
  promptPreview?: string | null;
  category?: string;
  jobId?: string | null;
};

export function buildMockGenerationSteps() {
  return GENERATION_PROGRESS_STAGES.map((stage) => ({
    percent: stage.max,
    message: stage.label,
    stageIndex: GENERATION_PROGRESS_STAGES.indexOf(stage),
  }));
}

/** Showcase category video matched loosely by category id. */
export function mockVideoUrlForCategory(category?: string): string {
  const key = (category ?? "").toLowerCase();
  if (key.includes("rap") || key.includes("song") || key.includes("music")) {
    return "/showcase/rap.mp4";
  }
  if (key.includes("business") || key.includes("commercial") || key.includes("ad")) {
    return "/showcase/commercial.mp4";
  }
  if (key.includes("cartoon") || key.includes("kids") || key.includes("anim")) {
    return "/showcase/cartoon.mp4";
  }
  if (key.includes("religious") || key.includes("islam") || key.includes("faith")) {
    return "/showcase/islamic.mp4";
  }
  if (key.includes("podcast") || key.includes("solo") || key.includes("talk")) {
    return "/showcase/solo.mp4";
  }
  return PRIMARY_SHOWCASE_STREAM_URL;
}

export function buildMockGenerationSuccess(input: MockGenerationInput) {
  const jobId = input.jobId?.trim() || `mock-${randomUUID()}`;
  const videoUrl = mockVideoUrlForCategory(input.category);

  return {
    status: "success" as const,
    ok: true,
    jobId,
    videoUrl,
    durationSeconds: input.durationSeconds,
    creditsUsed: 0,
    previewOnly: true,
    canDownload: false,
    simulationMode: true,
    promptPreview: input.promptPreview ?? null,
    message: "Preview render ready (studio simulation — GPU worker offline).",
    steps: buildMockGenerationSteps(),
  };
}

export function shouldFallbackToMockGeneration(proxy: {
  ok: boolean;
  status: number;
  data: Record<string, unknown>;
}): boolean {
  if (proxy.ok) return false;
  const code = proxy.data.code;
  if (code === "FASTAPI_URL_NOT_CONFIGURED") return true;
  if (proxy.status === 503 || proxy.status === 504 || proxy.status === 502) {
    return true;
  }
  const err = String(proxy.data.error ?? "").toLowerCase();
  return (
    err.includes("not configured") ||
    err.includes("connection error") ||
    err.includes("ensure the api") ||
    err.includes("timed out") ||
    err.includes("bad response")
  );
}

/**
 * RTAS Studio AI — FastAPI client (Next.js ↔ Python backend)
 */

export const BACKEND_CONNECTION_ERROR =
  "Backend server connection error. Please ensure the API service is running.";

export const FAL_AUTH_ERROR =
  "Fal.ai rejected this request. Check FAL_KEY in apps/backend/.env, or add billing credit at https://fal.ai/dashboard/billing (zero balance can also block generation).";

export const FAL_AUTH_HINT =
  "Open apps/backend/.env and confirm FAL_KEY, then add credit at https://fal.ai/dashboard/billing if balance is zero. Restart the API server and refresh this page.";

export const FAL_CREDIT_ERROR =
  "Insufficient Fal.ai balance. Add billing credit at https://fal.ai/dashboard/billing then try again.";

export const FAL_CREDIT_HINT =
  "Open Fal.ai billing, add credit, wait a few minutes, then generate again.";

export const REPLICATE_AUTH_ERROR =
  "Invalid Replicate API Token. Please check your config.";

export const REPLICATE_AUTH_HINT =
  "Set REPLICATE_API_TOKEN in apps/backend/.env or apps/api/.env, then restart the FastAPI server.";

export const REPLICATE_CREDIT_ERROR =
  "Insufficient Replicate credit. Add billing credit at https://replicate.com/account/billing then try again.";

export const REPLICATE_CREDIT_HINT =
  "Open Replicate billing, purchase credit, wait a few minutes, then generate again.";

const DEFAULT_FASTAPI_URL = "http://localhost:8000";

export function getFastApiBase(): string {
  const url = process.env.NEXT_PUBLIC_FASTAPI_URL?.trim();
  return (url || DEFAULT_FASTAPI_URL).replace(/\/$/, "");
}

export type BackendProcessingStep = {
  percent: number;
  message: string;
  stageIndex: number;
};

export type StudioFileMeta = {
  name: string;
  mimeType: string;
  size: number;
  localPath?: string;
  url?: string;
};

export type GenerateRequestBody = {
  jobId?: string;
  mode: string;
  category: string;
  visualStyle: string;
  durationSeconds: number;
  fields: Record<string, string>;
  files: Record<string, StudioFileMeta>;
  identityPipeline: Record<string, unknown>;
  profile?: {
    subscriptionActive: boolean;
    credits: number;
    freeTrialUsed: boolean;
    hasUsedFreeTrial?: boolean;
    tier?: string;
  };
  previewOnly?: boolean;
  useFreeTrial?: boolean;
  deviceFingerprint?: string;
  userId?: string;
};

export type UploadAssetsResponse = {
  ok: boolean;
  jobId: string;
  files: Record<
    string,
    StudioFileMeta & { fieldId?: string }
  >;
};

/** Files with a live `File` blob ready for multipart upload */
export type UploadableFile = {
  file: File;
  name: string;
  mimeType: string;
  size: number;
};

export function collectUploadableFiles(
  files: Record<string, UploadableFile | null | undefined>
): Record<string, UploadableFile> {
  const out: Record<string, UploadableFile> = {};
  for (const [id, v] of Object.entries(files)) {
    if (v?.file) out[id] = v;
  }
  return out;
}

export function mergeUploadedFileMeta(
  base: Record<string, StudioFileMeta>,
  uploaded: UploadAssetsResponse["files"]
): Record<string, StudioFileMeta> {
  const merged = { ...base };
  for (const [fieldId, info] of Object.entries(uploaded)) {
    merged[fieldId] = {
      name: info.name,
      mimeType: info.mimeType,
      size: info.size,
      localPath: info.localPath,
      url: info.url,
    };
  }
  return merged;
}

export async function postUploadToBackend(
  files: Record<string, UploadableFile>,
  jobId?: string
): Promise<UploadAssetsResponse> {
  const base = getFastApiBase();
  const formData = new FormData();
  if (jobId) formData.append("job_id", jobId);

  for (const [fieldId, meta] of Object.entries(files)) {
    formData.append(fieldId, meta.file, meta.name);
  }

  let res: Response;
  try {
    res = await fetch(`${base}/api/upload`, {
      method: "POST",
      body: formData,
      signal: AbortSignal.timeout(120_000),
    });
  } catch {
    throw new BackendConnectionError();
  }

  let data: Record<string, unknown>;
  try {
    data = (await res.json()) as Record<string, unknown>;
  } catch {
    if (!res.ok) throw new BackendConnectionError();
    throw new Error("Invalid upload response from API");
  }

  if (!res.ok) {
    const detail = data.detail;
    if (res.status >= 500) throw new BackendConnectionError();
    const msg =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail
              .map((d) =>
                typeof d === "object" && d && "msg" in d
                  ? String((d as { msg: string }).msg)
                  : ""
              )
              .filter(Boolean)
              .join(", ")
          : String(data.error ?? "Upload failed");
    throw new Error(msg);
  }

  const filesRaw = (data.files as Record<string, Record<string, unknown>>) ?? {};
  const normalizedFiles: UploadAssetsResponse["files"] = {};
  for (const [fieldId, raw] of Object.entries(filesRaw)) {
    normalizedFiles[fieldId] = {
      name: String(raw.name ?? ""),
      mimeType: String(raw.mimeType ?? raw.mime_type ?? ""),
      size: Number(raw.size ?? 0),
      localPath: String(raw.localPath ?? raw.local_path ?? ""),
      url: raw.url ? String(raw.url) : undefined,
      fieldId: String(raw.fieldId ?? raw.field_id ?? fieldId),
    };
  }

  return {
    ok: Boolean(data.ok ?? true),
    jobId: String(data.jobId ?? data.job_id ?? ""),
    files: normalizedFiles,
  };
}

export type BackendGenerateResponse = {
  ok: boolean;
  jobId: string;
  steps: BackendProcessingStep[];
  provider: string;
  promptPreview: string;
  creditsUsed: number;
  previewOnly: boolean;
  canDownload: boolean;
  videoUrl: string;
  durationSeconds: number;
  message: string;
  simulationMode?: boolean;
};

export class BackendConnectionError extends Error {
  constructor(message = BACKEND_CONNECTION_ERROR) {
    super(message);
    this.name = "BackendConnectionError";
  }
}

export class FalAuthError extends Error {
  constructor(message = FAL_AUTH_ERROR) {
    super(message);
    this.name = "FalAuthError";
  }
}

export class FalCreditError extends Error {
  constructor(message = FAL_CREDIT_ERROR) {
    super(message);
    this.name = "FalCreditError";
  }
}

export class ReplicateAuthError extends Error {
  constructor(message = REPLICATE_AUTH_ERROR) {
    super(message);
    this.name = "ReplicateAuthError";
  }
}

export class ReplicateCreditError extends Error {
  constructor(message = REPLICATE_CREDIT_ERROR) {
    super(message);
    this.name = "ReplicateCreditError";
  }
}

export function isBackendConnectionError(err: unknown): boolean {
  return err instanceof BackendConnectionError;
}

export function isFalAuthError(err: unknown): boolean {
  return err instanceof FalAuthError;
}

export function isFalCreditError(err: unknown): boolean {
  return err instanceof FalCreditError;
}

export function isReplicateAuthError(err: unknown): boolean {
  return err instanceof ReplicateAuthError;
}

export function isReplicateCreditError(err: unknown): boolean {
  return err instanceof ReplicateCreditError;
}

function isFalAuthMessage(message: string): boolean {
  const lower = message.toLowerCase();
  return (
    lower.includes("invalid fal.ai api key") ||
    lower.includes("fal.ai api key") ||
    lower.includes("fal_key")
  );
}

function isFalCreditMessage(message: string): boolean {
  const lower = message.toLowerCase();
  const markers = [
    "exhausted balance",
    "user is locked",
    "top up your balance",
    "insufficient fal.ai balance",
    "insufficient balance",
    "out of credits",
    "zero balance",
    "add billing credit",
  ];
  if (markers.some((m) => lower.includes(m))) return true;
  return lower.includes("insufficient") && lower.includes("fal");
}

function isReplicateAuthMessage(message: string): boolean {
  const lower = message.toLowerCase();
  return (
    lower.includes("invalid replicate api token") ||
    lower.includes("unauthorized") ||
    lower.includes("invalid token") ||
    lower.includes("auth error")
  );
}

function isReplicateCreditMessage(message: string): boolean {
  const lower = message.toLowerCase();
  return lower.includes("insufficient replicate credit") || lower.includes("insufficient credit");
}

function extractApiErrorMessage(
  data: Record<string, unknown>,
  fallback = "Generation failed"
): string {
  const detail = data.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const joined = detail
      .map((d) =>
        typeof d === "object" && d && "msg" in d
          ? String((d as { msg: string }).msg)
          : ""
      )
      .filter(Boolean)
      .join(", ");
    if (joined) return joined;
  }
  const error = data.error;
  if (typeof error === "string" && error.trim()) return error;
  return fallback;
}

export type FalGuardStatus = {
  billingBlocked: boolean;
  blockedReason: string | null;
  retryAfterSec: number;
  liveCallsAllowed: boolean;
  liveEnabled: boolean;
};

export type BackendHealthStatus = {
  online: boolean;
  primaryProvider: string | null;
  falConfigured: boolean;
  falValid: boolean | null;
  falError: string | null;
  falLiveGeneration: boolean;
  falGuard: FalGuardStatus | null;
  replicateConfigured: boolean;
  replicateValid: boolean | null;
  replicateError: string | null;
};

function normalizeFalGuard(
  raw: Record<string, unknown> | undefined
): FalGuardStatus | null {
  if (!raw) return null;
  return {
    billingBlocked: Boolean(raw.billing_blocked),
    blockedReason:
      typeof raw.blocked_reason === "string" ? raw.blocked_reason : null,
    retryAfterSec: Number(raw.retry_after_sec ?? 0),
    liveCallsAllowed: Boolean(raw.live_calls_allowed),
    liveEnabled: Boolean(raw.live_enabled ?? true),
  };
}

function normalizeStep(raw: Record<string, unknown>): BackendProcessingStep {
  return {
    percent: Number(raw.percent ?? 0),
    message: String(raw.message ?? ""),
    stageIndex: Number(raw.stageIndex ?? raw.stage_index ?? 0),
  };
}

function normalizeResponse(data: Record<string, unknown>): BackendGenerateResponse {
  const stepsRaw = (data.steps as Record<string, unknown>[]) ?? [];
  return {
    ok: Boolean(data.ok ?? true),
    jobId: String(data.jobId ?? data.job_id ?? ""),
    steps: stepsRaw.map((s) => normalizeStep(s)),
    provider: String(data.provider ?? "rtas"),
    promptPreview: String(data.promptPreview ?? data.prompt_preview ?? ""),
    creditsUsed: Number(data.creditsUsed ?? data.credits_used ?? 0),
    previewOnly: Boolean(data.previewOnly ?? data.preview_only),
    canDownload: Boolean(data.canDownload ?? data.can_download),
    videoUrl: String(data.videoUrl ?? data.video_url ?? ""),
    durationSeconds: Number(data.durationSeconds ?? data.duration_seconds ?? 30),
    message: String(data.message ?? "Generation complete"),
    simulationMode: Boolean(data.simulationMode ?? data.simulation_mode ?? false),
  };
}

/** Quick health probe (optional UI indicator) */
export async function checkBackendHealth(): Promise<boolean> {
  const status = await fetchBackendHealthStatus();
  return status.online;
}

export async function fetchBackendHealthStatus(): Promise<BackendHealthStatus> {
  const offline: BackendHealthStatus = {
    online: false,
    primaryProvider: null,
    falConfigured: false,
    falValid: null,
    falError: null,
    falLiveGeneration: false,
    falGuard: null,
    replicateConfigured: false,
    replicateValid: null,
    replicateError: null,
  };
  try {
    const base = getFastApiBase();
    const pingRes = await fetch(`${base}/api/health/ping`, {
      method: "GET",
      signal: AbortSignal.timeout(5_000),
    });
    if (!pingRes.ok) return offline;

    const res = await fetch(`${base}/api/health`, {
      method: "GET",
      signal: AbortSignal.timeout(8_000),
    });
    if (!res.ok) {
      const pingData = (await pingRes.json()) as Record<string, unknown>;
      const pingFal = (pingData.fal as Record<string, unknown> | undefined) ?? {};
      return {
        online: true,
        primaryProvider: null,
        falConfigured: Boolean(pingFal.configured),
        falValid: null,
        falError: null,
        falLiveGeneration: false,
        falGuard: null,
        replicateConfigured: false,
        replicateValid: null,
        replicateError: null,
      };
    }
    const data = (await res.json()) as Record<string, unknown>;
    const fal = (data.fal as Record<string, unknown> | undefined) ?? {};
    const replicate = (data.replicate as Record<string, unknown> | undefined) ?? {};
    const guard = normalizeFalGuard(
      (fal.guard as Record<string, unknown> | undefined) ?? undefined
    );
    return {
      online: true,
      primaryProvider:
        typeof data.primary_provider === "string" ? data.primary_provider : null,
      falConfigured: Boolean(fal.configured),
      falValid: typeof fal.valid === "boolean" ? fal.valid : null,
      falError: typeof fal.error === "string" ? fal.error : null,
      falLiveGeneration: Boolean(fal.live_generation),
      falGuard: guard,
      replicateConfigured: Boolean(replicate.configured),
      replicateValid:
        typeof replicate.valid === "boolean" ? replicate.valid : null,
      replicateError:
        typeof replicate.error === "string" ? replicate.error : null,
    };
  } catch {
    return offline;
  }
}

export async function postGenerateToBackend(
  body: GenerateRequestBody
): Promise<BackendGenerateResponse> {
  const base = getFastApiBase();
  const url = `${base}/api/generate`;

  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(120_000),
    });
  } catch {
    throw new BackendConnectionError();
  }

  let data: Record<string, unknown>;
  try {
    data = (await res.json()) as Record<string, unknown>;
  } catch {
    if (!res.ok) throw new BackendConnectionError();
    throw new Error("Invalid response from API");
  }

  if (!res.ok) {
    const msg = extractApiErrorMessage(data);
    console.error("Fal API Error:", msg);
    

    if (res.status === 409) {
      throw new Error(
        msg || "A video generation is already in progress. Please wait for it to finish."
      );
    }

    if (isFalAuthMessage(msg)) {
      throw new FalAuthError(FAL_AUTH_ERROR);
    }
    if (isReplicateAuthMessage(msg)) {
      throw new ReplicateAuthError(
        isReplicateAuthMessage(msg) ? REPLICATE_AUTH_ERROR : msg
      );
    }
    if (res.status === 401) {
      throw new Error(msg || "Unauthorized request to RTAS API");
    }
    if (
      res.status === 403 &&
      (msg.toLowerCase().includes("free trial") ||
        msg.toLowerCase().includes("device/network"))
    ) {
      throw new Error(msg);
    }
    if (res.status === 402 || isFalCreditMessage(msg) || isReplicateCreditMessage(msg)) {
      if (isFalCreditMessage(msg)) {
        throw new FalCreditError(FAL_CREDIT_ERROR);
      }
      throw new ReplicateCreditError(
        isReplicateCreditMessage(msg) ? REPLICATE_CREDIT_ERROR : msg
      );
    }
    if (res.status >= 500 || res.status === 0) {
      if (isFalCreditMessage(msg)) {
        throw new FalCreditError(FAL_CREDIT_ERROR);
      }
      if (isFalAuthMessage(msg)) {
        throw new FalAuthError(FAL_AUTH_ERROR);
      }
      if (msg && msg !== "Generation failed") {
        throw new Error(msg);
      }
      throw new BackendConnectionError();
    }
    throw new Error(msg);
  }

  return normalizeResponse(data);
}

export type ProgressHandler = (step: BackendProcessingStep) => void;

/**
 * POST /api/generate then drive GenerationProgressOverlay from returned steps.
 */
export async function runBackendGeneration(
  body: GenerateRequestBody,
  onProgress: ProgressHandler,
  options?: {
    animationMs?: number;
    /** Raw form files — uploaded via multipart before /api/generate */
    uploadables?: Record<string, UploadableFile | null | undefined>;
  }
): Promise<BackendGenerateResponse> {
  onProgress({
    percent: 0,
    message: "Connecting to RTAS AI API…",
    stageIndex: 0,
  });

  let requestBody = body;
  const toUpload = options?.uploadables
    ? collectUploadableFiles(options.uploadables)
    : {};
  if (Object.keys(toUpload).length > 0) {
    onProgress({
      percent: 3,
      message: "Uploading audio & images to RTAS API…",
      stageIndex: 0,
    });
    const uploadRes = await postUploadToBackend(toUpload, body.jobId);
    requestBody = {
      ...body,
      jobId: uploadRes.jobId,
      files: mergeUploadedFileMeta(body.files, uploadRes.files),
    };
  }

  const response = await postGenerateToBackend(requestBody);

  if (!response.steps?.length) {
    onProgress({
      percent: 100,
      message: response.message || "Complete",
      stageIndex: 3,
    });
    return response;
  }

  await playBackendSteps(response.steps, onProgress, options?.animationMs ?? 6500);
  return response;
}

/** Map backend `steps[]` into overlay state (~6s playback) */
export async function playBackendSteps(
  steps: BackendProcessingStep[],
  onProgress: ProgressHandler,
  totalMs = 6500
): Promise<void> {
  if (steps.length === 0) return;

  const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));
  const stepMs = Math.max(25, Math.floor(totalMs / steps.length));
  let lastPercent = -1;

  for (const s of steps) {
    if (s.percent !== lastPercent) {
      onProgress(s);
      lastPercent = s.percent;
      await delay(stepMs);
    }
  }
}

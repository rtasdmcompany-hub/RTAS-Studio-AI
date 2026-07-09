import { LONG_VIDEO_THRESHOLD_SECONDS } from "@rtas/shared";
import { getServerFastApiBase } from "@/lib/server/fastapi-proxy";
import { generationJobCallbackUrl } from "@/lib/server/generation-webhook";

export function shouldUseAsyncPipeline(input: {
  durationSeconds: number;
  previewOnly?: boolean;
  useFreeTrial?: boolean;
}): boolean {
  if (input.previewOnly || input.useFreeTrial) return false;
  return input.durationSeconds > LONG_VIDEO_THRESHOLD_SECONDS;
}

export async function triggerAsyncGpuPipeline(
  body: Record<string, unknown>,
  pipelineJobId: string
): Promise<{ ok: boolean; error?: string; status?: number }> {
  const base = getServerFastApiBase();
  if (!base) {
    return { ok: false, error: "GPU worker is not configured" };
  }

  const callbackUrl = generationJobCallbackUrl(pipelineJobId);
  const backendJobId = body.jobId ?? pipelineJobId;
  const payload = {
    ...body,
    jobId: backendJobId,
    pipelineJobId,
    statusCallbackUrl: callbackUrl,
  };

  try {
    const res = await fetch(`${base}/api/generate/async`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(30_000),
    });

    if (!res.ok) {
      let message = "Failed to queue GPU worker";
      try {
        const data = (await res.json()) as { detail?: string; error?: string };
        message = data.detail ?? data.error ?? message;
      } catch {
        // ignore parse errors
      }
      return { ok: false, error: message, status: res.status };
    }

    return { ok: true };
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Failed to reach GPU worker";
    return { ok: false, error: message };
  }
}

import type { PipelineFailurePayload } from "@/lib/pipeline-errors";

export function buildGpuPipelineFailure(
  httpStatus: number,
  message: string,
  options?: { timedOut?: boolean }
): PipelineFailurePayload {
  const details = message.trim() || "Unknown GPU pipeline error";
  const lower = details.toLowerCase();

  if (options?.timedOut || httpStatus === 504) {
    return {
      status: "failed",
      error: "GPU Pipeline Timeout",
      details,
      code: "GPU_TIMEOUT",
    };
  }

  if (httpStatus === 502) {
    return {
      status: "failed",
      error: "GPU Bad Gateway",
      details,
      code: "BAD_GATEWAY",
    };
  }

  if (httpStatus === 503) {
    return {
      status: "failed",
      error: "GPU Backend Offline",
      details,
      code: "BACKEND_OFFLINE",
    };
  }

  if (
    httpStatus === 403 &&
    (lower.includes("content") ||
      lower.includes("policy") ||
      lower.includes("moderation") ||
      lower.includes("safety"))
  ) {
    return {
      status: "failed",
      error: "Prompt Safety Filter",
      details,
      code: "CONTENT_POLICY",
    };
  }

  if (httpStatus === 409) {
    return {
      status: "failed",
      error: "GPU Render Queue Busy",
      details,
      code: "RENDER_IN_PROGRESS",
    };
  }

  if (httpStatus === 402) {
    return {
      status: "failed",
      error: "GPU Provider Billing Block",
      details,
      code: "PROVIDER_BILLING",
    };
  }

  if (httpStatus >= 500) {
    return {
      status: "failed",
      error: "GPU Pipeline Runtime Error",
      details,
      code: "GPU_RUNTIME",
    };
  }

  return {
    status: "failed",
    error: "GPU Pipeline Rejected",
    details,
    code: "GPU_REJECTED",
  };
}

export function httpStatusForPipelineFailure(
  failure: PipelineFailurePayload,
  upstreamStatus: number
): number {
  if (failure.code === "GPU_TIMEOUT" || failure.code === "BAD_GATEWAY") {
    return 400;
  }
  if (upstreamStatus === 403 || upstreamStatus === 409) {
    return 400;
  }
  if (upstreamStatus >= 500) {
    return 400;
  }
  return 400;
}

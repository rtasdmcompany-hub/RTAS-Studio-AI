import { resolveServerFastApiUrl } from "@/lib/env";

const FASTAPI_NOT_CONFIGURED_RESPONSE = {
  error:
    "GPU worker is not configured. Set FASTAPI_URL in server environment variables.",
  code: "FASTAPI_URL_NOT_CONFIGURED" as const,
};

export function getServerFastApiBase(): string | null {
  const resolved = resolveServerFastApiUrl();
  return resolved.ok ? resolved.url : null;
}

/** Service-to-service secret for FastAPI (never expose to the browser). */
function backendSecretHeaders(): Record<string, string> {
  const secret =
    process.env.AI_BACKEND_SECRET?.trim() ||
    process.env.RTAS_BACKEND_SECRET?.trim() ||
    "";
  if (!secret) return {};
  return { "X-Rtas-Backend-Secret": secret };
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

function isTimeoutError(err: unknown): boolean {
  if (!(err instanceof Error)) return false;
  return (
    err.name === "TimeoutError" ||
    err.name === "AbortError" ||
    /timeout|timed out|aborted/i.test(err.message)
  );
}

export async function proxyGenerateToFastApi(
  body: Record<string, unknown>
): Promise<{
  ok: boolean;
  status: number;
  data: Record<string, unknown>;
  timedOut?: boolean;
}> {
  const base = getServerFastApiBase();
  if (!base) {
    return {
      ok: false,
      status: 503,
      data: FASTAPI_NOT_CONFIGURED_RESPONSE,
    };
  }

  const url = `${base}/api/generate`;

  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...backendSecretHeaders(),
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(120_000),
    });
  } catch (err) {
    const timedOut = isTimeoutError(err);
    return {
      ok: false,
      status: timedOut ? 504 : 503,
      timedOut,
      data: {
        error: timedOut
          ? "GPU render exceeded the maximum wait window."
          : "Backend server connection error. Please ensure the API service is running.",
      },
    };
  }

  let data: Record<string, unknown>;
  try {
    data = (await res.json()) as Record<string, unknown>;
  } catch {
    if (!res.ok) {
      return {
        ok: false,
        status: res.status === 502 || res.status === 504 ? res.status : 503,
        data: {
          error:
            res.status === 504
              ? "GPU gateway timed out while waiting for the render worker."
              : res.status === 502
                ? "GPU gateway returned a bad response."
                : "Backend server connection error. Please ensure the API service is running.",
        },
      };
    }
    return {
      ok: false,
      status: 500,
      data: { error: "Invalid response from generation service" },
    };
  }

  if (!res.ok) {
    return {
      ok: false,
      status: res.status,
      data: { error: extractApiErrorMessage(data), ...data },
    };
  }

  return { ok: true, status: res.status, data };
}

export async function proxyUploadToFastApi(
  formData: FormData
): Promise<{ ok: boolean; status: number; data: Record<string, unknown> }> {
  const base = getServerFastApiBase();
  if (!base) {
    return {
      ok: false,
      status: 503,
      data: FASTAPI_NOT_CONFIGURED_RESPONSE,
    };
  }

  const url = `${base}/api/upload`;

  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: {
        ...backendSecretHeaders(),
      },
      body: formData,
      signal: AbortSignal.timeout(120_000),
    });
  } catch {
    return {
      ok: false,
      status: 503,
      data: {
        error:
          "Backend server connection error. Please ensure the API service is running.",
      },
    };
  }

  let data: Record<string, unknown>;
  try {
    data = (await res.json()) as Record<string, unknown>;
  } catch {
    if (!res.ok) {
      return {
        ok: false,
        status: 503,
        data: {
          error:
            "Backend server connection error. Please ensure the API service is running.",
        },
      };
    }
    return {
      ok: false,
      status: 500,
      data: { error: "Invalid response from upload service" },
    };
  }

  if (!res.ok) {
    return {
      ok: false,
      status: res.status,
      data: { error: extractApiErrorMessage(data, "Upload failed"), ...data },
    };
  }

  return { ok: true, status: res.status, data };
}

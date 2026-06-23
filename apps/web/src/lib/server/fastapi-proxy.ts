const DEFAULT_FASTAPI_URL = "http://localhost:8000";

export function getServerFastApiBase(): string {
  const url =
    process.env.FASTAPI_URL?.trim() ||
    process.env.NEXT_PUBLIC_FASTAPI_URL?.trim();
  return (url || DEFAULT_FASTAPI_URL).replace(/\/$/, "");
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

export async function proxyGenerateToFastApi(
  body: Record<string, unknown>
): Promise<{ ok: boolean; status: number; data: Record<string, unknown> }> {
  const url = `${getServerFastApiBase()}/api/generate`;

  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(120_000),
    });
  } catch {
    return {
      ok: false,
      status: 503,
      data: { error: "Backend server connection error. Please ensure the API service is running." },
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
        data: { error: "Backend server connection error. Please ensure the API service is running." },
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
  const url = `${getServerFastApiBase()}/api/upload`;

  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
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

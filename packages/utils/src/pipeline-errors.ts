export type PipelineFailurePayload = {
  status: "failed";
  error: string;
  details: string;
  code?: string;
};

export class PipelineFailureError extends Error {
  readonly details: string;
  readonly code?: string;

  constructor(error: string, details: string, code?: string) {
    super(error);
    this.name = "PipelineFailureError";
    this.details = details;
    this.code = code;
  }
}

export function isPipelineFailurePayload(
  data: unknown
): data is PipelineFailurePayload {
  if (typeof data !== "object" || data === null) return false;
  const record = data as Record<string, unknown>;
  return record.status === "failed" && typeof record.error === "string";
}

export function isPipelineFailureError(err: unknown): err is PipelineFailureError {
  return err instanceof PipelineFailureError;
}

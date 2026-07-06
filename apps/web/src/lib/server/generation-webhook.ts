import { getNextAuthUrl } from "@/lib/env";

export function getGenerationWebhookSecret(): string | null {
  const explicit = process.env.RTAS_GENERATION_WEBHOOK_SECRET?.trim();
  if (explicit) return explicit;
  const backend = process.env.AI_BACKEND_SECRET?.trim();
  return backend || null;
}

export function verifyGenerationWebhook(request: Request): boolean {
  const secret = getGenerationWebhookSecret();
  if (!secret) return false;

  const auth = request.headers.get("authorization");
  const header = request.headers.get("x-rtas-generation-secret");
  return auth === `Bearer ${secret}` || header === secret;
}

export function generationJobCallbackUrl(jobId: string): string {
  const base = getNextAuthUrl().replace(/\/$/, "");
  return `${base}/api/generate/jobs/${jobId}`;
}

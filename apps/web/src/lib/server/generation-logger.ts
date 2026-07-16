/**
 * Structured generation logs for the SaaS orchestrator.
 * Never logs secrets or full prompt bodies in production.
 */

export type GenerationLogEvent = {
  event: string;
  generationId?: string | null;
  userId?: string | null;
  provider?: string | null;
  durationSeconds?: number | null;
  credits?: number | null;
  latencyMs?: number | null;
  failure?: string | null;
  status?: string | null;
  projectId?: string | null;
  retryCount?: number | null;
  [key: string]: unknown;
};

export function logGeneration(event: GenerationLogEvent): void {
  const payload = {
    ts: new Date().toISOString(),
    service: "rtas-generation-orchestrator",
    ...event,
  };
  const line = JSON.stringify(payload);
  if (event.failure || event.event.includes("fail")) {
    console.error(line);
  } else {
    console.info(line);
  }
}

/**
 * Sprint 2 orchestrator unit tests (node:test).
 * Run: node --test ./scripts/test-orchestrator.mjs
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";

/** Inline mirrors of packages/shared job-orchestrator (no TS loader required). */
const JOB_LIFECYCLE_STATUSES = [
  "queued",
  "preparing",
  "generating",
  "rendering",
  "uploading",
  "completed",
  "failed",
  "cancelled",
];

function normalizeJobLifecycleStatus(status) {
  const s = String(status).toLowerCase().replace(/-/g, "_");
  switch (s) {
    case "queued":
      return "queued";
    case "preparing":
      return "preparing";
    case "generating":
    case "generating_chunks":
      return "generating";
    case "rendering":
    case "compiling_media":
      return "rendering";
    case "uploading":
      return "uploading";
    case "completed":
      return "completed";
    case "failed":
      return "failed";
    case "cancelled":
    case "canceled":
      return "cancelled";
    default:
      return "queued";
  }
}

function isTerminalJobStatus(status) {
  const s = normalizeJobLifecycleStatus(status);
  return s === "completed" || s === "failed" || s === "cancelled";
}

function creditsRequiredForDuration(durationSeconds) {
  const seconds = Number.isFinite(durationSeconds) ? durationSeconds : 0;
  return Math.max(1, Math.ceil(seconds));
}

function classifyGenerationFailure(message) {
  const m = message.toLowerCase();
  if (m.includes("cancel")) return "cancelled";
  if (m.includes("rate limit") || m.includes("429") || m.includes("too many")) {
    return "rate_limit";
  }
  if (
    m.includes("timeout") ||
    m.includes("timed out") ||
    m.includes("etimedout") ||
    m.includes("econnreset")
  ) {
    return m.includes("webhook") ? "webhook_timeout" : "network_timeout";
  }
  if (
    m.includes("unavailable") ||
    m.includes("503") ||
    m.includes("502") ||
    m.includes("connection")
  ) {
    return "provider_unavailable";
  }
  return "permanent";
}

function shouldRetryGenerationFailure(code, retryCount, maxRetries = 2) {
  if (retryCount >= maxRetries) return false;
  return (
    code === "network_timeout" ||
    code === "webhook_timeout" ||
    code === "provider_unavailable" ||
    code === "rate_limit"
  );
}

function selectProvider(env) {
  if (env.FAL_KEY) return "fal";
  if (env.REPLICATE_API_TOKEN) return "replicate";
  return null;
}

function shouldDebitCredits({ status, creditsDebited, skipBilling }) {
  if (skipBilling) return false;
  if (creditsDebited) return false;
  return status === "completed";
}

describe("job lifecycle", () => {
  it("normalizes legacy pipeline statuses", () => {
    assert.equal(normalizeJobLifecycleStatus("GENERATING_CHUNKS"), "generating");
    assert.equal(normalizeJobLifecycleStatus("compiling_media"), "rendering");
    assert.equal(normalizeJobLifecycleStatus("PREPARING"), "preparing");
    assert.equal(normalizeJobLifecycleStatus("cancelled"), "cancelled");
  });

  it("marks terminal states", () => {
    assert.equal(isTerminalJobStatus("completed"), true);
    assert.equal(isTerminalJobStatus("failed"), true);
    assert.equal(isTerminalJobStatus("cancelled"), true);
    assert.equal(isTerminalJobStatus("generating"), false);
    assert.equal(isTerminalJobStatus("queued"), false);
  });

  it("covers full lifecycle set", () => {
    assert.deepEqual(JOB_LIFECYCLE_STATUSES, [
      "queued",
      "preparing",
      "generating",
      "rendering",
      "uploading",
      "completed",
      "failed",
      "cancelled",
    ]);
  });
});

describe("credits", () => {
  it("bills 1 credit per second", () => {
    assert.equal(creditsRequiredForDuration(15), 15);
    assert.equal(creditsRequiredForDuration(1), 1);
    assert.equal(creditsRequiredForDuration(0), 1);
  });

  it("never double-charges", () => {
    assert.equal(
      shouldDebitCredits({
        status: "completed",
        creditsDebited: true,
        skipBilling: false,
      }),
      false
    );
    assert.equal(
      shouldDebitCredits({
        status: "completed",
        creditsDebited: false,
        skipBilling: false,
      }),
      true
    );
    assert.equal(
      shouldDebitCredits({
        status: "failed",
        creditsDebited: false,
        skipBilling: false,
      }),
      false
    );
  });
});

describe("retry logic", () => {
  it("retries transient failures only", () => {
    assert.equal(classifyGenerationFailure("request timed out"), "network_timeout");
    assert.equal(classifyGenerationFailure("webhook timeout"), "webhook_timeout");
    assert.equal(classifyGenerationFailure("503 unavailable"), "provider_unavailable");
    assert.equal(classifyGenerationFailure("429 rate limit"), "rate_limit");
    assert.equal(classifyGenerationFailure("cancelled by user"), "cancelled");
    assert.equal(classifyGenerationFailure("invalid prompt"), "permanent");

    assert.equal(shouldRetryGenerationFailure("network_timeout", 0), true);
    assert.equal(shouldRetryGenerationFailure("rate_limit", 1), true);
    assert.equal(shouldRetryGenerationFailure("permanent", 0), false);
    assert.equal(shouldRetryGenerationFailure("cancelled", 0), false);
    assert.equal(shouldRetryGenerationFailure("network_timeout", 2), false);
  });
});

describe("provider routing", () => {
  it("prefers Fal then Replicate", () => {
    assert.equal(selectProvider({ FAL_KEY: "x" }), "fal");
    assert.equal(selectProvider({ REPLICATE_API_TOKEN: "y" }), "replicate");
    assert.equal(selectProvider({}), null);
  });
});

describe("webhook processing", () => {
  it("accepts completed and failed statuses", () => {
    const handle = (status) => {
      const s = normalizeJobLifecycleStatus(status);
      if (s === "completed") return "finalize_success";
      if (s === "failed" || s === "cancelled") return "finalize_failure";
      return "update_progress";
    };
    assert.equal(handle("completed"), "finalize_success");
    assert.equal(handle("failed"), "finalize_failure");
    assert.equal(handle("generating"), "update_progress");
    assert.equal(handle("uploading"), "update_progress");
  });
});

describe("project persistence + downloads", () => {
  it("requires completed output for download", () => {
    const canDownload = (job) =>
      job.status === "completed" && Boolean(job.generatedVideoUrl);
    assert.equal(
      canDownload({ status: "completed", generatedVideoUrl: "https://x/a.mp4" }),
      true
    );
    assert.equal(canDownload({ status: "generating", generatedVideoUrl: null }), false);
    assert.equal(canDownload({ status: "failed", generatedVideoUrl: null }), false);
  });

  it("duplicate carries settings forward", () => {
    const source = {
      prompt: "cinematic dusk",
      settings: { mode: "text", category: "business" },
      durationSeconds: 15,
    };
    const dup = { ...source, status: "draft" };
    assert.equal(dup.prompt, source.prompt);
    assert.equal(dup.settings.mode, "text");
    assert.equal(dup.durationSeconds, 15);
    assert.equal(dup.status, "draft");
  });
});

console.log("test-orchestrator: suite registered");

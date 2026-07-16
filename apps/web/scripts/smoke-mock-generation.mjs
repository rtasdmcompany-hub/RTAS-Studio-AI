/**
 * Smoke: production must reject mock generation unless ALLOW_MOCK_GENERATION=true.
 * Run: node ./scripts/smoke-mock-generation.mjs
 */
import assert from "node:assert/strict";

function isMockGenerationAllowed(env) {
  if (env.ALLOW_MOCK_GENERATION === "true") return true;
  if (env.ALLOW_MOCK_GENERATION === "false") return false;
  return env.NODE_ENV !== "production";
}

function creditsRequiredForDuration(durationSeconds) {
  const seconds = Number.isFinite(durationSeconds) ? durationSeconds : 0;
  return Math.max(1, Math.ceil(seconds));
}

assert.equal(isMockGenerationAllowed({ NODE_ENV: "production" }), false);
assert.equal(
  isMockGenerationAllowed({ NODE_ENV: "production", ALLOW_MOCK_GENERATION: "true" }),
  true
);
assert.equal(isMockGenerationAllowed({ NODE_ENV: "development" }), true);
assert.equal(
  isMockGenerationAllowed({ NODE_ENV: "development", ALLOW_MOCK_GENERATION: "false" }),
  false
);

assert.equal(creditsRequiredForDuration(15), 15);
assert.equal(creditsRequiredForDuration(1), 1);
assert.equal(creditsRequiredForDuration(0), 1);
assert.equal(creditsRequiredForDuration(15.2), 16);

console.log("smoke-mock-generation: ok");

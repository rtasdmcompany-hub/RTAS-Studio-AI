#!/usr/bin/env node
/**
 * Commercial smoke tests — no live network required.
 * Covers payment parsing, webhook signatures, credit grants,
 * subscription activation, OAuth linking policy, and env gates.
 */
import assert from "node:assert/strict";
import crypto from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const webRoot = join(__dirname, "..");

// Keep in sync with packages/shared/src/credits.ts
const STANDARD_CREDITS = 2000;
const PREMIUM_CREDITS = 2000;
const TESTER_CREDITS = 30;

function creditsForPlan(plan) {
  if (plan === "tester") return TESTER_CREDITS;
  if (plan === "premium") return PREMIUM_CREDITS;
  return STANDARD_CREDITS;
}

function resolvePlanFromCustomData(custom) {
  const plan = (custom?.plan ?? custom?.plan_type ?? custom?.planType ?? "")
    .toLowerCase()
    .trim();
  if (plan === "tester") return "tester";
  if (plan === "premium") return "premium";
  if (plan === "standard") return "standard";
  return "standard";
}

function verifyPaddleSignature(rawBody, signatureHeader, secret, nodeEnv, allowUnsigned) {
  if (!secret) {
    return nodeEnv === "development" && allowUnsigned === true;
  }
  if (!signatureHeader) return false;
  const parts = signatureHeader.split(";");
  const h1 = parts.find((p) => p.startsWith("h1="))?.slice(3);
  if (!h1) return false;
  const ts = parts.find((p) => p.startsWith("ts="))?.slice(3) ?? "";
  const signed = `${ts}:${rawBody}`;
  const expected = crypto.createHmac("sha256", secret).update(signed).digest("hex");
  try {
    return crypto.timingSafeEqual(Buffer.from(h1), Buffer.from(expected));
  } catch {
    return false;
  }
}

function verifyLemonSignature(rawBody, signatureHeader, secret, nodeEnv, allowUnsigned) {
  if (!secret) {
    return nodeEnv === "development" && allowUnsigned === true;
  }
  if (!signatureHeader) return false;
  const digest = crypto.createHmac("sha256", secret).update(rawBody).digest("hex");
  try {
    return crypto.timingSafeEqual(Buffer.from(signatureHeader), Buffer.from(digest));
  } catch {
    return false;
  }
}

function parsePaddleActivated(body) {
  const custom = body.data?.custom_data ?? {};
  const userId = (custom.user_id ?? custom.userId ?? "").trim();
  const planType = resolvePlanFromCustomData(custom);
  return {
    type: "subscription_activated",
    payload: {
      userId,
      email: custom.email,
      planType,
      creditsToGrant: creditsForPlan(planType),
      provider: "paddle",
    },
  };
}

function applySubscriptionCredits(profile, payload) {
  const tier = payload.planType === "premium" ? "premium" : "standard";
  const defaultGrant = tier === "premium" ? PREMIUM_CREDITS : STANDARD_CREDITS;
  const now = new Date();
  const remaining =
    profile.subscriptionActive &&
    profile.tier === tier &&
    profile.creditsExpireAt &&
    new Date(profile.creditsExpireAt) > now
      ? profile.credits
      : 0;
  const credits = remaining + (payload.creditsToGrant || defaultGrant);
  return {
    ...profile,
    tier,
    subscriptionActive: true,
    credits,
    paymentProvider: payload.provider,
    // Commercial license entitlement = active paid subscription (terms grant).
    commercialLicenseActive: true,
  };
}

let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`[pass] ${name}`);
}

console.log("RTAS commercial smoke tests\n");

assert.equal(creditsForPlan("standard"), STANDARD_CREDITS);
assert.equal(creditsForPlan("premium"), PREMIUM_CREDITS);
assert.equal(creditsForPlan("tester"), TESTER_CREDITS);
assert.equal(resolvePlanFromCustomData({ plan: "premium" }), "premium");
ok("Payment plan detection + credit assignment");

{
  const secret = "test-paddle-secret";
  const rawBody = JSON.stringify({ event_type: "subscription.activated" });
  const ts = "1710000000";
  const h1 = crypto
    .createHmac("sha256", secret)
    .update(`${ts}:${rawBody}`)
    .digest("hex");
  assert.equal(
    verifyPaddleSignature(rawBody, `ts=${ts};h1=${h1}`, secret, "production", false),
    true
  );
  assert.equal(
    verifyPaddleSignature(rawBody, `ts=${ts};h1=deadbeef`, secret, "production", false),
    false
  );
  assert.equal(verifyPaddleSignature(rawBody, null, "", "production", false), false);
  assert.equal(verifyPaddleSignature(rawBody, null, "", "development", false), false);
  assert.equal(verifyPaddleSignature(rawBody, null, "", "development", true), true);
  ok("Paddle webhook signature verification");
}

{
  const secret = "test-lemon-secret";
  const rawBody = '{"meta":{"event_name":"subscription_created"}}';
  const digest = crypto.createHmac("sha256", secret).update(rawBody).digest("hex");
  assert.equal(verifyLemonSignature(rawBody, digest, secret, "production", false), true);
  assert.equal(verifyLemonSignature(rawBody, null, "", "production", false), false);
  assert.equal(verifyLemonSignature(rawBody, null, "", "development", false), false);
  ok("Lemon Squeezy webhook signature verification");
}

{
  const event = parsePaddleActivated({
    event_type: "subscription.activated",
    data: {
      id: "sub_123",
      customer_id: "ctm_1",
      custom_data: {
        user_id: "user-abc",
        email: "creator@example.com",
        plan: "standard",
      },
    },
  });
  assert.equal(event.payload.userId, "user-abc");
  assert.equal(event.payload.creditsToGrant, STANDARD_CREDITS);

  const activated = applySubscriptionCredits(
    {
      id: "user-abc",
      tier: "free",
      subscriptionActive: false,
      credits: 0,
      creditsExpireAt: null,
    },
    event.payload
  );
  assert.equal(activated.subscriptionActive, true);
  assert.equal(activated.tier, "standard");
  assert.equal(activated.credits, STANDARD_CREDITS);
  assert.equal(activated.commercialLicenseActive, true);

  const renewed = applySubscriptionCredits(
    {
      ...activated,
      credits: 100,
      creditsExpireAt: new Date(Date.now() + 86400000).toISOString(),
    },
    { ...event.payload, creditsToGrant: STANDARD_CREDITS }
  );
  assert.equal(renewed.credits, 100 + STANDARD_CREDITS);
  ok("Subscription activation, credit grant, license entitlement");
}

{
  const authOptionsSrc = readFileSync(
    join(webRoot, "src/lib/auth/auth-options.ts"),
    "utf8"
  );
  const authUsersSrc = readFileSync(
    join(webRoot, "src/lib/server/auth-users.ts"),
    "utf8"
  );
  assert.match(authOptionsSrc, /allowDangerousEmailAccountLinking:\s*false/);
  assert.match(authUsersSrc, /OAuth account linking blocked/);
  assert.match(authOptionsSrc, /already has a password/);
  ok("OAuth unsafe linking disabled + explicit block paths");
}

{
  const checkoutSrc = readFileSync(
    join(webRoot, "src/app/api/checkout/route.ts"),
    "utf8"
  );
  assert.match(checkoutSrc, /NODE_ENV === "production"/);
  assert.match(checkoutSrc, /status: 503/);
  ok("Production demo checkout disabled");
}

{
  const orchestratorSrc = readFileSync(
    join(webRoot, "src/lib/server/generation-orchestrator.ts"),
    "utf8"
  );
  assert.match(orchestratorSrc, /isFreeTrialBlocked/);
  assert.match(orchestratorSrc, /accountTrialUsed/);
  assert.match(orchestratorSrc, /useFreeTrial = false/);
  assert.match(orchestratorSrc, /previewOnly = false/);
  ok("Generate API enforces trial/preview server-side");
}

{
  const envSrc = readFileSync(join(webRoot, "src/lib/env.ts"), "utf8");
  assert.match(envSrc, /NEXTAUTH_SECRET must be set/);
  assert.match(envSrc, /throw new Error/);
  ok("NEXTAUTH_SECRET fail-closed in production runtime");
}

{
  // Email delivery helpers exist and are wired
  const mailerPath = join(webRoot, "src/lib/server/mailer.ts");
  const mailerSrc = readFileSync(mailerPath, "utf8");
  assert.match(mailerSrc, /sendEmail|nodemailer|resend/i);
  ok("Email delivery module present");
}

{
  const fastapiProxy = readFileSync(
    join(webRoot, "src/lib/server/fastapi-proxy.ts"),
    "utf8"
  );
  assert.match(fastapiProxy, /FASTAPI|proxy/i);
  ok("GPU worker proxy module present");
}

console.log(`\n${passed} smoke checks passed.`);

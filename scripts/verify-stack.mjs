#!/usr/bin/env node
/**
 * End-to-end stack verification for RTAS Studio AI dev environment.
 */
const API = process.env.FASTAPI_URL || "http://localhost:8000";
const WEB = process.env.WEB_URL || "http://localhost:3000";
const ADMIN_ID = process.env.ADMIN_USER_ID || "";

const checks = [];

function pass(name, detail = "") {
  checks.push({ name, ok: true, detail });
  console.log(`✓ ${name}${detail ? ` — ${detail}` : ""}`);
}

function fail(name, detail = "") {
  checks.push({ name, ok: false, detail });
  console.error(`✗ ${name}${detail ? ` — ${detail}` : ""}`);
}

async function fetchJson(url, timeoutMs = 15_000) {
  const res = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) });
  const text = await res.text();
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    json = { _raw: text };
  }
  return { ok: res.ok, status: res.status, json };
}

async function main() {
  console.log("\nRTAS Studio AI — Stack Verification\n");

  // 1. Fast ping
  try {
    const ping = await fetchJson(`${API}/api/health/ping`, 5_000);
    if (ping.ok && ping.json.status === "healthy") {
      pass("Backend ping", `${API}/api/health/ping`);
    } else {
      fail("Backend ping", `HTTP ${ping.status}`);
    }
  } catch (e) {
    fail("Backend ping", String(e));
  }

  // 2. Full health
  try {
    const health = await fetchJson(`${API}/api/health`, 10_000);
    if (health.ok) {
      const fal = health.json.fal || {};
      pass(
        "Backend health",
        `fal.configured=${fal.configured} fal.valid=${fal.valid} live=${fal.live_generation}`
      );
      if (!fal.configured) fail("Fal configured", "FAL_KEY missing in backend .env");
      if (fal.valid === false) fail("Fal valid", fal.error || "invalid key");
    } else {
      fail("Backend health", `HTTP ${health.status}`);
    }
  } catch (e) {
    fail("Backend health", String(e));
  }

  // 3. Frontend
  try {
    const home = await fetch(WEB, { signal: AbortSignal.timeout(30_000) });
    if (home.ok) pass("Frontend home", WEB);
    else fail("Frontend home", `HTTP ${home.status}`);
  } catch (e) {
    fail("Frontend home", String(e));
  }

  // 4. Auth config bridge
  try {
    const cfg = await fetchJson(`${WEB}/api/auth/config`, 30_000);
    if (cfg.ok) {
      pass(
        "Auth config bridge",
        `simulationMode=${cfg.json.simulationMode} falConfigured=${cfg.json.falConfigured}`
      );
      if (cfg.json.simulationMode) fail("Simulation mode", "should be false when Fal is configured");
    } else {
      fail("Auth config bridge", `HTTP ${cfg.status}`);
    }
  } catch (e) {
    fail("Auth config bridge", String(e));
  }

  // 5. Optional premium profile check
  if (ADMIN_ID) {
    try {
      const sub = await fetchJson(`${WEB}/api/user/subscription?userId=${ADMIN_ID}`, 15_000);
      if (sub.ok) {
        pass(
          "Admin premium profile",
          `tier=${sub.json.tier} credits=${sub.json.credits} active=${sub.json.subscriptionActive}`
        );
      } else {
        fail("Admin premium profile", `HTTP ${sub.status}`);
      }
    } catch (e) {
      fail("Admin premium profile", String(e));
    }
  } else {
    pass("Admin premium profile", "skipped (set ADMIN_USER_ID to enable)");
  }

  // 6. Optional trial abuse check
  if (ADMIN_ID) {
    try {
      const trial = await fetch(`${WEB}/api/trial/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId: ADMIN_ID, deviceFingerprint: "audit-test-fp" }),
        signal: AbortSignal.timeout(15_000),
      });
      const trialJson = await trial.json();
      if (trial.ok && trialJson.allowed) {
        pass("Trial abuse verify", "allowed for fresh device");
      } else {
        fail("Trial abuse verify", trialJson.message || `HTTP ${trial.status}`);
      }
    } catch (e) {
      fail("Trial abuse verify", String(e));
    }
  } else {
    pass("Trial abuse verify", "skipped (set ADMIN_USER_ID to enable)");
  }

  // 7. Env key presence (no secret printed)
  try {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const { fileURLToPath } = await import("node:url");
    const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
    const envPaths = [
      path.join(root, "apps", "backend", ".env"),
      path.join(root, "apps", "web", ".env.local"),
    ];
    for (const p of envPaths) {
      const label = path.relative(root, p);
      if (!fs.existsSync(p)) {
        fail(`Env file ${label}`, "missing");
        continue;
      }
      const content = fs.readFileSync(p, "utf8");
      const match = content.match(/^FAL_KEY=(.+)$/m);
      const value = match?.[1]?.trim();
      if (!value) {
        fail(`Env FAL_KEY ${label}`, "empty or missing");
      } else if (value.length < 20 || value.includes("your_")) {
        fail(`Env FAL_KEY ${label}`, "looks like placeholder");
      } else {
        pass(`Env FAL_KEY ${label}`, "present");
      }
    }
  } catch (e) {
    fail("Env key audit", String(e));
  }

  const failed = checks.filter((c) => !c.ok);
  console.log(`\n${checks.length - failed.length}/${checks.length} checks passed\n`);
  process.exit(failed.length > 0 ? 1 : 0);
}

main();

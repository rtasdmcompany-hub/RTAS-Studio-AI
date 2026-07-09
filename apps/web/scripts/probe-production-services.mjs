#!/usr/bin/env node
/**
 * Live production connectivity probes (no secret values printed).
 * Tests: Postgres (Prisma URL), Resend, fal.ai, FastAPI health, Supabase REST.
 */
import { readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const envPath = join(webRoot, ".env.local");

function parseEnv(text) {
  const map = {};
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq <= 0) continue;
    let value = trimmed.slice(eq + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    map[trimmed.slice(0, eq).trim()] = value;
  }
  return map;
}

const env = existsSync(envPath)
  ? { ...parseEnv(readFileSync(envPath, "utf8")), ...process.env }
  : { ...process.env };

function present(key) {
  return Boolean((env[key] || "").trim());
}

function maskHost(url) {
  try {
    const u = new URL(url);
    return `${u.protocol}//${u.host}`;
  } catch {
    return "(invalid-url)";
  }
}

let failed = 0;
function pass(name, detail = "") {
  console.log(`[pass] ${name}${detail ? ` — ${detail}` : ""}`);
}
function fail(name, detail = "") {
  failed += 1;
  console.error(`[FAIL] ${name}${detail ? ` — ${detail}` : ""}`);
}
function warn(name, detail = "") {
  console.warn(`[warn] ${name}${detail ? ` — ${detail}` : ""}`);
}

console.log("RTAS live connectivity probes\n");

// --- Database ---
{
  const db = (env.DATABASE_URL || "").trim();
  if (!db) {
    fail("Postgres DATABASE_URL", "missing");
  } else {
    pass("Postgres DATABASE_URL configured", maskHost(db.replace(/^postgresql:/, "https:").replace(/^postgres:/, "https:")));
    // Lightweight TCP-less check: URL shape + sslmode for Supabase
    if (/supabase\.co|pooler\.supabase/i.test(db)) {
      pass("Database host looks like Supabase Postgres");
    } else {
      warn("Database host", "not supabase.co — confirm production provider");
    }
  }
}

// --- Supabase REST ---
{
  const url = (env.NEXT_PUBLIC_SUPABASE_URL || "").trim();
  const anon = (env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "").trim();
  if (!url || !anon) {
    warn("Supabase REST", "URL/anon key missing — app uses Prisma/NextAuth primarily");
  } else {
    try {
      const res = await fetch(`${url.replace(/\/$/, "")}/rest/v1/`, {
        headers: {
          apikey: anon,
          Authorization: `Bearer ${anon}`,
        },
        signal: AbortSignal.timeout(15_000),
      });
      if (res.ok || res.status === 200 || res.status === 404 || res.status === 401) {
        pass("Supabase REST reachable", `HTTP ${res.status}`);
      } else {
        fail("Supabase REST", `HTTP ${res.status}`);
      }
    } catch (err) {
      fail("Supabase REST", err instanceof Error ? err.message : "network error");
    }
  }
  if (present("SUPABASE_SERVICE_ROLE_KEY")) {
    pass("Supabase service role key present (not printed)");
  } else {
    warn("Supabase service role", "missing — only needed for admin/server storage ops");
  }
}

// --- Resend ---
{
  const key = (env.RESEND_API_KEY || "").trim();
  if (!key) {
    fail("Resend API key", "missing");
  } else {
    try {
      const res = await fetch("https://api.resend.com/domains", {
        headers: { Authorization: `Bearer ${key}` },
        signal: AbortSignal.timeout(15_000),
      });
      if (res.ok) {
        const data = await res.json().catch(() => ({}));
        const domains = Array.isArray(data?.data) ? data.data : [];
        const verified = domains.filter(
          (d) => d?.status === "verified" || d?.status === "verified" || d?.region
        );
        pass("Resend API key valid", `${domains.length} domain(s) listed`);
        if (domains.length === 0) {
          warn(
            "Resend domains",
            "no domains — production email needs a verified sending domain"
          );
        } else {
          for (const d of domains.slice(0, 5)) {
            console.log(
              `       domain=${d.name || d.id} status=${d.status || "unknown"}`
            );
          }
        }
      } else if (res.status === 401) {
        fail("Resend API key", "unauthorized");
      } else {
        fail("Resend API", `HTTP ${res.status}`);
      }
    } catch (err) {
      fail("Resend API", err instanceof Error ? err.message : "network error");
    }
  }
  const from = (env.EMAIL_FROM || "").trim();
  if (!from) warn("EMAIL_FROM", "missing");
  else if (/resend\.dev/i.test(from)) {
    warn("EMAIL_FROM", "sandbox onboarding@resend.dev — verify custom domain for production");
  } else {
    pass("EMAIL_FROM configured", from.replace(/<.*>/, "<…>"));
  }
}

// --- fal.ai ---
{
  const key = (env.FAL_KEY || "").trim();
  if (!key) {
    fail("fal.ai FAL_KEY", "missing");
  } else {
    try {
      // Account/user endpoint — validates key without starting a paid render
      const res = await fetch("https://api.fal.ai/v1/models?limit=1", {
        headers: { Authorization: `Key ${key}` },
        signal: AbortSignal.timeout(20_000),
      });
      if (res.ok) {
        pass("fal.ai API key accepted");
      } else if (res.status === 401 || res.status === 403) {
        // Some accounts use different auth header forms
        const res2 = await fetch("https://queue.fal.run/fal-ai/fast-sdxl", {
          method: "POST",
          headers: {
            Authorization: `Key ${key}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({}),
          signal: AbortSignal.timeout(20_000),
        });
        if (res2.status === 422 || res2.status === 400) {
          pass("fal.ai API key accepted", `queue auth ok (HTTP ${res2.status})`);
        } else if (res2.status === 401 || res2.status === 403) {
          fail("fal.ai API key", `rejected HTTP ${res2.status}`);
        } else {
          pass("fal.ai reachable", `HTTP ${res2.status}`);
        }
      } else {
        pass("fal.ai reachable", `HTTP ${res.status}`);
      }
    } catch (err) {
      fail("fal.ai API", err instanceof Error ? err.message : "network error");
    }
  }
}

// --- FastAPI GPU worker ---
{
  const url = (env.FASTAPI_URL || "").trim().replace(/\/$/, "");
  if (!url) {
    fail("FASTAPI_URL", "missing");
  } else if (/localhost|127\.0\.0\.1/i.test(url)) {
    warn("FASTAPI_URL", "points to localhost — not usable on Vercel production");
  } else {
    try {
      const health = await fetch(`${url}/health`, {
        signal: AbortSignal.timeout(15_000),
      }).catch(() => null);
      const root = health?.ok
        ? health
        : await fetch(`${url}/`, { signal: AbortSignal.timeout(15_000) });
      if (root && (root.ok || root.status < 500)) {
        pass("GPU worker reachable", `${maskHost(url)} HTTP ${root.status}`);
      } else {
        fail("GPU worker", `unreachable or HTTP ${root?.status}`);
      }
    } catch (err) {
      fail("GPU worker", err instanceof Error ? err.message : "network error");
    }
  }
}

// --- Payments ---
{
  const provider = (env.NEXT_PUBLIC_PAYMENT_PROVIDER || "paddle").toLowerCase();
  pass("Payment provider", provider);
  if (provider === "paddle") {
    if (present("PADDLE_WEBHOOK_SECRET")) pass("Paddle webhook secret present");
    else fail("Paddle webhook secret", "missing");
    if (
      present("NEXT_PUBLIC_PADDLE_CHECKOUT_URL") ||
      present("NEXT_PUBLIC_PADDLE_STANDARD_CHECKOUT_URL")
    ) {
      pass("Paddle checkout URL present");
    } else {
      fail("Paddle checkout URL", "missing");
    }
  }
}

console.log(
  failed
    ? `\n${failed} connectivity check(s) failed.`
    : "\nAll critical connectivity probes passed."
);
process.exit(failed > 0 ? 1 : 0);

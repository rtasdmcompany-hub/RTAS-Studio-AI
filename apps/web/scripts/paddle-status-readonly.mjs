#!/usr/bin/env node
/** Read-only Paddle + env status (no transaction creation). */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

function parseEnv(text) {
  const map = new Map();
  for (const line of text.split(/\r?\n/)) {
    const t = line.trim();
    if (!t || t.startsWith("#")) continue;
    const eq = t.indexOf("=");
    if (eq <= 0) continue;
    let v = t.slice(eq + 1).trim();
    if (
      (v.startsWith('"') && v.endsWith('"')) ||
      (v.startsWith("'") && v.endsWith("'"))
    ) {
      v = v.slice(1, -1);
    }
    map.set(t.slice(0, eq).trim(), v);
  }
  return map;
}

const vars = parseEnv(readFileSync(resolve(".env.local"), "utf8"));
const key = (vars.get("PADDLE_API_KEY") || "").trim();

const env = {
  provider: vars.get("NEXT_PUBLIC_PAYMENT_PROVIDER") || "(unset)",
  deferPaddle: vars.get("RTAS_DEFER_PADDLE") || "(unset)",
  hasApiKey: Boolean(key),
  hasClientToken: Boolean(vars.get("NEXT_PUBLIC_PADDLE_CLIENT_TOKEN")),
  hasWebhook: Boolean(vars.get("PADDLE_WEBHOOK_SECRET")),
  hasTesterPrice: Boolean(vars.get("PADDLE_TESTER_PRICE_ID")),
  hasStandardPrice: Boolean(vars.get("PADDLE_STANDARD_PRICE_ID")),
  hasPremiumPrice: Boolean(vars.get("PADDLE_PREMIUM_PRICE_ID")),
};

if (!key) {
  console.log(JSON.stringify({ ok: false, env, error: "PADDLE_API_KEY missing" }));
  process.exit(1);
}

const products = await fetch("https://api.paddle.com/products?per_page=10", {
  headers: { Authorization: `Bearer ${key}` },
});
const prices = await fetch("https://api.paddle.com/prices?per_page=20", {
  headers: { Authorization: `Bearer ${key}` },
});
const pj = await products.json().catch(() => ({}));
const prj = await prices.json().catch(() => ({}));

console.log(
  JSON.stringify({
    ok: products.ok && prices.ok,
    env,
    products: {
      status: products.status,
      count: Array.isArray(pj.data) ? pj.data.length : 0,
      names: (pj.data || []).slice(0, 5).map((p) => p.name),
    },
    prices: {
      status: prices.status,
      count: Array.isArray(prj.data) ? prj.data.length : 0,
    },
    apiError: products.ok ? null : pj?.error?.detail || pj?.error?.code || "products-failed",
  })
);

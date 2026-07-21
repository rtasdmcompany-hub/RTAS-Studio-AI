#!/usr/bin/env node
/** Probe whether live Paddle checkouts are enabled (creates then cancels if needed). */
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
const price = (vars.get("PADDLE_TESTER_PRICE_ID") || "").trim();

if (!key || !price) {
  console.log(JSON.stringify({ ok: false, error: "missing key or tester price" }));
  process.exit(1);
}

const headers = {
  Authorization: `Bearer ${key}`,
  "Content-Type": "application/json",
};

const res = await fetch("https://api.paddle.com/transactions", {
  method: "POST",
  headers,
  body: JSON.stringify({
    items: [{ price_id: price, quantity: 1 }],
    collection_mode: "automatic",
    custom_data: { probe: "checkout_gate" },
  }),
});
const json = await res.json().catch(() => ({}));

const out = {
  status: res.status,
  code: json.error?.code || null,
  detail: json.error?.detail || null,
  docs: json.error?.documentation_url || null,
  transactionId: json.data?.id || null,
  hasCheckoutUrl: Boolean(json.data?.checkout?.url),
  checkoutEnabled: res.ok && Boolean(json.data?.checkout?.url),
};

console.log(JSON.stringify(out, null, 2));

// Soft-delete / leave draft — do not collect payment. If created, mark as cancelled if API allows.
if (json.data?.id && json.data?.status === "draft") {
  // nothing required
}

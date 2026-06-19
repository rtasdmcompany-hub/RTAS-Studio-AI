/**
 * Test Gmail SMTP from apps/web/.env.local
 * Usage: node scripts/test-smtp.mjs your@gmail.com
 */
import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const envPath = join(__dirname, "..", ".env.local");

function readEnvFile(path) {
  if (!existsSync(path)) return {};
  const map = {};
  for (const line of readFileSync(path, "utf8").split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const idx = trimmed.indexOf("=");
    if (idx === -1) continue;
    const key = trimmed.slice(0, idx).trim();
    let value = trimmed.slice(idx + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    map[key] = value;
  }
  return map;
}

const env = readEnvFile(envPath);
const to = process.argv[2] || env.SMTP_USER;
const host = env.SMTP_HOST || "smtp.gmail.com";
const port = Number(env.SMTP_PORT || 587);
const user = env.SMTP_USER;
const pass = env.SMTP_PASS;
const from = env.EMAIL_FROM || `"RTAS STUDIO AI" <${user}>`;

if (!user || !pass) {
  console.error("SMTP_USER and SMTP_PASS must be set in apps/web/.env.local");
  console.error("Gmail: Google Account → Security → App passwords → paste in SMTP_PASS");
  process.exit(1);
}

if (!to) {
  console.error("Usage: node scripts/test-smtp.mjs recipient@gmail.com");
  process.exit(1);
}

const nodemailer = await import("nodemailer");
const transport = nodemailer.createTransport({
  host,
  port,
  secure: env.SMTP_SECURE === "true" || port === 465,
  auth: { user, pass },
});

console.log("Verifying SMTP connection…");
await transport.verify();
console.log("SMTP OK. Sending test email to", to);

await transport.sendMail({
  from,
  to,
  subject: "RTAS STUDIO AI — SMTP test",
  text: "If you received this, Gmail SMTP is working for RTAS Studio AI.",
  html: "<p>If you received this, <strong>Gmail SMTP is working</strong> for RTAS Studio AI.</p>",
});

console.log("Test email sent successfully.");

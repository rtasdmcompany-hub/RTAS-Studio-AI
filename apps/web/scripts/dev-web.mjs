#!/usr/bin/env node
/**
 * Start Next.js dev server with logs in the current terminal (Cursor-friendly).
 * Bypasses external CMD launcher windows.
 */
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

console.log("");
console.log("========================================");
console.log("  RTAS Studio AI — Web Dev Server");
console.log("========================================");
console.log(`  Directory: ${webRoot}`);
console.log("  URL:       http://localhost:3000");
console.log("========================================");
console.log("");

const command =
  process.platform === "win32" ? "npm.cmd run dev:fast" : "npm run dev:fast";

const child = spawn(command, {
  cwd: webRoot,
  stdio: "inherit",
  env: process.env,
  shell: true,
});

child.on("error", (err) => {
  console.error("[RTAS] Failed to start dev server:", err.message);
  process.exit(1);
});

child.on("exit", (code) => {
  process.exit(code ?? 1);
});

#!/usr/bin/env node
/**
 * Start FastAPI backend with logs in the current terminal (Cursor-friendly).
 */
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const backendRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  "backend"
);
const python =
  process.platform === "win32"
    ? path.join(backendRoot, ".venv", "Scripts", "python.exe")
    : path.join(backendRoot, ".venv", "bin", "python");

console.log("");
console.log("========================================");
console.log("  RTAS Studio AI — FastAPI Backend");
console.log("========================================");
console.log(`  Directory: ${backendRoot}`);
console.log("  URL:       http://localhost:8000");
console.log("========================================");
console.log("");

if (!fs.existsSync(python)) {
  console.error(`[RTAS] Python venv not found: ${python}`);
  console.error("Run once: cd apps/backend && python -m venv .venv && pip install -r requirements.txt");
  process.exit(1);
}

const child = spawn(
  python,
  ["-m", "uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
  { cwd: backendRoot, stdio: "inherit", env: process.env }
);

child.on("error", (err) => {
  console.error("[RTAS] Failed to start API:", err.message);
  process.exit(1);
});

child.on("exit", (code) => {
  process.exit(code ?? 1);
});

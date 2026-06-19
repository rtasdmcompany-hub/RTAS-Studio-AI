#!/usr/bin/env node
/**
 * Start FastAPI with the project venv Python (Windows + Unix).
 */
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const backend = path.join(root, "apps", "backend");
const python =
  process.platform === "win32"
    ? path.join(backend, ".venv", "Scripts", "python.exe")
    : path.join(backend, ".venv", "bin", "python");

if (!fs.existsSync(python)) {
  console.error(`[error] venv Python not found: ${python}`);
  console.error("Run: cd apps/backend && python -m venv .venv && pip install -r requirements.txt");
  process.exit(1);
}

const child = spawn(
  python,
  ["-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
  { cwd: backend, stdio: "inherit", env: process.env }
);

child.on("exit", (code) => process.exit(code ?? 1));

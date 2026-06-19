/**
 * Dry-run: paths, FFmpeg, stitcher script, output clip count.
 * Run from apps/web: node scripts/verify-compile-setup.mjs
 */
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const backendRoot = path.resolve(webRoot, "..", "backend");
const outputsDir = path.join(backendRoot, "data", "outputs");
const stitcherScript = path.join(backendRoot, "video_stitcher.py");

function isSourceClip(name) {
  const lower = name.toLowerCase();
  return (
    lower.endsWith(".mp4") &&
    !name.includes("_compiled") &&
    !name.startsWith("compiled_5min")
  );
}

console.log("=== RTAS Compile dry-run ===");
console.log("web cwd (expected apps/web):", webRoot);
console.log("backend root:", backendRoot);
console.log("outputs dir:", outputsDir);
console.log("stitcher script:", stitcherScript);

const stitcherOk = fs.existsSync(stitcherScript);
console.log("stitcher exists:", stitcherOk ? "yes" : "NO");

if (!fs.existsSync(outputsDir)) {
  fs.mkdirSync(outputsDir, { recursive: true });
  console.log("outputs dir: created");
}

let clips = [];
try {
  clips = fs.readdirSync(outputsDir).filter(isSourceClip);
} catch (e) {
  console.error("outputs read error:", e.message);
}

console.log("source clips in outputs:", clips.length);
console.log("min required for compile: 10");

const ff = spawnSync("ffmpeg", ["-version"], { encoding: "utf8" });
if (ff.error || ff.status !== 0) {
  console.log("ffmpeg: MISSING");
  console.log(
    process.platform === "win32"
      ? "Install: choco install ffmpeg -y"
      : "Install: sudo apt-get update && sudo apt-get install -y ffmpeg"
  );
  process.exitCode = 1;
} else {
  const firstLine = (ff.stdout || "").split("\n")[0];
  console.log("ffmpeg:", firstLine || "ok");
}

if (!stitcherOk) process.exitCode = 1;
console.log("=== done ===");

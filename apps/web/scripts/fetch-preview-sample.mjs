#!/usr/bin/env node
/**
 * Downloads a cinematic showcase MP4 into public/video/preview-showcase.mp4
 */
import { existsSync, mkdirSync, unlinkSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const outDir = join(__dirname, "..", "public", "video");
const outFile = join(outDir, "preview-showcase.mp4");
const legacyFile = join(outDir, "preview-sample.mp4");

const REMOTE_URLS = [
  "https://videos.pexels.com/video-files/4058822/4058822-uhd_2560_1440_25fps.mp4",
  "https://videos.pexels.com/video-files/857251/857251-uhd_2560_1440_24fps.mp4",
  "https://samplelib.com/lib/preview/mp4/sample-30s.mp4",
  "https://samplelib.com/lib/preview/mp4/sample-5s.mp4",
  "https://assets.mixkit.co/videos/preview/mixkit-singer-with-microphone-in-a-concert-4172-large.mp4",
  "https://assets.mixkit.co/videos/preview/mixkit-aerial-panorama-of-a-landscape-4241-large.mp4",
];

const force = process.argv.includes("--force");

async function main() {
  if (existsSync(outFile) && !force) {
    console.log("[skip] cinematic showcase already exists:", outFile);
    return;
  }

  mkdirSync(outDir, { recursive: true });

  if (force && existsSync(outFile)) {
    unlinkSync(outFile);
  }

  for (const url of REMOTE_URLS) {
    try {
      console.log("[fetch]", url);
      const res = await fetch(url, { signal: AbortSignal.timeout(180_000) });
      if (!res.ok) continue;
      const buf = Buffer.from(await res.arrayBuffer());
      if (buf.length < 500_000) continue;
      writeFileSync(outFile, buf);
      console.log("[ok] Saved cinematic showcase:", outFile, `(${Math.round(buf.length / 1024 / 1024)} MB)`);
      if (existsSync(legacyFile)) {
        try {
          unlinkSync(legacyFile);
          console.log("[ok] Removed legacy bunny sample:", legacyFile);
        } catch {
          /* ignore */
        }
      }
      return;
    } catch (err) {
      console.warn("[warn] failed:", url, err instanceof Error ? err.message : err);
    }
  }

  console.warn(
    "[warn] Could not download preview-showcase.mp4 — VideoPlayer will use remote cinematic fallbacks."
  );
}

main();

import { NextResponse } from "next/server";
import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import {
  MIN_COMPILE_CLIPS,
  ensureOutputsDir,
  getCompilePaths,
  getCompiledVideoUrl,
  isCompileSourceClip,
  listOutputClipFiles,
} from "@/lib/compile-paths";

function checkFfmpegAvailable(): Promise<boolean> {
  return new Promise((resolve) => {
    const cmd = process.platform === "win32" ? "ffmpeg" : "ffmpeg";
    const child = spawn(cmd, ["-version"], { windowsHide: true });
    child.on("error", () => resolve(false));
    child.on("close", (code) => resolve(code === 0));
  });
}

function runVideoStitcher(
  stitcherScript: string,
  outputPath: string,
  outputsDir: string,
  options?: { inputFiles?: string[]; targetDurationSec?: number }
): Promise<{ ok: boolean; output?: string; clip_count?: number; error?: string }> {
  return new Promise((resolve, reject) => {
    const pythonCmd = process.platform === "win32" ? "python" : "python3";
    const args = [
      stitcherScript,
      "--output",
      outputPath,
      "--outputs-dir",
      outputsDir,
      "--duration",
      String(options?.targetDurationSec ?? 300),
    ];

    if (options?.inputFiles?.length) {
      for (const file of options.inputFiles) {
        args.push("--inputs", path.join(outputsDir, file));
      }
    }

    const child = spawn(pythonCmd, args, {
      cwd: path.dirname(stitcherScript),
      windowsHide: true,
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk: Buffer) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk: Buffer) => {
      stderr += chunk.toString();
    });

    child.on("error", (err) => {
      reject(err);
    });

    child.on("close", (code) => {
      if (code !== 0) {
        const detail = stderr.trim() || stdout.trim() || `exit ${code}`;
        console.error("Video stitcher error:", detail);
        try {
          const parsed = JSON.parse(detail) as { error?: string };
          resolve({ ok: false, error: parsed.error ?? "Video stitcher failed" });
        } catch {
          resolve({ ok: false, error: detail || "Video stitcher failed" });
        }
        return;
      }

      try {
        const parsed = JSON.parse(stdout.trim()) as {
          ok: boolean;
          output?: string;
          clip_count?: number;
          error?: string;
        };
        resolve(parsed);
      } catch {
        resolve({ ok: false, error: "Invalid stitcher response" });
      }
    });
  });
}

/** Status for Compile button — reads apps/backend/data/outputs clip count. */
export async function GET() {
  const paths = getCompilePaths();
  await ensureOutputsDir(paths.outputsDir);

  const [clips, ffmpegAvailable] = await Promise.all([
    listOutputClipFiles(paths.outputsDir),
    checkFfmpegAvailable(),
  ]);

  let stitcherReady = false;
  try {
    await fs.access(paths.stitcherScript);
    stitcherReady = true;
  } catch {
    stitcherReady = false;
  }

  return NextResponse.json({
    ok: true,
    clipCount: clips.length,
    minClips: MIN_COMPILE_CLIPS,
    canCompile:
      clips.length >= MIN_COMPILE_CLIPS && ffmpegAvailable && stitcherReady,
    outputsDir: paths.outputsDir,
    stitcherScript: paths.stitcherScript,
    stitcherReady,
    ffmpegAvailable,
  });
}

/** Merge output clips into one MP4 via apps/backend/video_stitcher.py. */
export async function POST(request: Request) {
  const paths = getCompilePaths();
  await ensureOutputsDir(paths.outputsDir);

  let body: { clipFiles?: string[]; targetDurationSec?: number } = {};
  try {
    body = (await request.json()) as typeof body;
  } catch {
    /* optional body — legacy compile-all mode */
  }

  const targetDurationSec = body.targetDurationSec ?? 300;
  const explicitClips = (body.clipFiles ?? []).filter(isCompileSourceClip);
  const clips =
    explicitClips.length > 0
      ? explicitClips
      : await listOutputClipFiles(paths.outputsDir);

  const minRequired =
    explicitClips.length > 0
      ? Math.max(2, explicitClips.length)
      : MIN_COMPILE_CLIPS;

  if (clips.length < minRequired) {
    return NextResponse.json(
      {
        error: `Need at least ${minRequired} clips to stitch (found ${clips.length}).`,
        clipCount: clips.length,
        minClips: minRequired,
        outputsDir: paths.outputsDir,
      },
      { status: 400 }
    );
  }

  const ffmpegAvailable = await checkFfmpegAvailable();
  if (!ffmpegAvailable) {
    const installHint =
      process.platform === "win32"
        ? "choco install ffmpeg -y"
        : "sudo apt-get update && sudo apt-get install -y ffmpeg";
    return NextResponse.json(
      {
        error: "FFmpeg is not installed or not on PATH.",
        installHint,
      },
      { status: 500 }
    );
  }

  try {
    await fs.access(paths.stitcherScript);
  } catch {
    return NextResponse.json(
      { error: "video_stitcher.py not found in apps/backend." },
      { status: 500 }
    );
  }

  const outputName = `compiled_5min_${Date.now()}.mp4`;
  const outputPath = path.join(paths.outputsDir, outputName);

  let result: Awaited<ReturnType<typeof runVideoStitcher>>;
  try {
    result = await runVideoStitcher(
      paths.stitcherScript,
      outputPath,
      paths.outputsDir,
      {
        inputFiles: explicitClips.length > 0 ? clips : undefined,
        targetDurationSec,
      }
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to run video stitcher";
    console.error("Compile stitcher spawn error:", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }

  if (!result.ok) {
    console.error("Video stitcher error:", result.error ?? "stitch failed");
    return NextResponse.json(
      { error: result.error ?? "Video stitching failed" },
      { status: 500 }
    );
  }

  const videoUrl = getCompiledVideoUrl(outputName);

  return NextResponse.json({
    ok: true,
    message: `Compiled ${result.clip_count ?? clips.length} clips into a ${Math.round(targetDurationSec / 60)}-minute video.`,
    videoUrl,
    clipCount: result.clip_count ?? clips.length,
    outputFile: outputName,
    outputsDir: paths.outputsDir,
    targetDurationSec,
  });
}

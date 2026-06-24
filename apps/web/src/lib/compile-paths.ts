import fs from "node:fs/promises";
import path from "node:path";
import { isServerlessRuntime } from "@/lib/server/data-dir";

/** Minimum clips in apps/backend/data/outputs before Compile is enabled. */
export const MIN_COMPILE_CLIPS = 10;

export type CompilePaths = {
  backendRoot: string;
  outputsDir: string;
  stitcherScript: string;
};

/** Resolve backend paths from Next.js app cwd (apps/web → apps/backend). */
export function getCompilePaths(): CompilePaths {
  if (isServerlessRuntime()) {
    const backendRoot = path.join("/tmp", "rtas-compile");
    return {
      backendRoot,
      outputsDir: path.join(backendRoot, "data", "outputs"),
      stitcherScript: path.join(backendRoot, "video_stitcher.py"),
    };
  }

  const backendRoot = path.resolve(process.cwd(), "..", "backend");
  return {
    backendRoot,
    outputsDir: path.join(backendRoot, "data", "outputs"),
    stitcherScript: path.join(backendRoot, "video_stitcher.py"),
  };
}

export function isCompileSourceClip(name: string): boolean {
  const lower = name.toLowerCase();
  return (
    lower.endsWith(".mp4") &&
    !name.includes("_compiled") &&
    !name.startsWith("compiled_5min")
  );
}

export async function listOutputClipFiles(outputsDir: string): Promise<string[]> {
  try {
    const names = await fs.readdir(outputsDir);
    return names.filter(isCompileSourceClip).sort();
  } catch {
    return [];
  }
}

export async function ensureOutputsDir(outputsDir: string): Promise<void> {
  await fs.mkdir(outputsDir, { recursive: true });
}

export function getCompiledVideoUrl(outputFileName: string): string {
  const apiBase =
    process.env.NEXT_PUBLIC_FASTAPI_URL?.replace(/\/$/, "") ||
    process.env.FASTAPI_URL?.replace(/\/$/, "") ||
    "http://localhost:8000";
  return `${apiBase}/media/outputs/${outputFileName}`;
}

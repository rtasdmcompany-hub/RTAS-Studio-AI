/** Standard / Premium long renders — split into 15-second segments, then stitch. */
export const VIDEO_SEGMENT_SECONDS = 15;

/** Durations above this use the multi-segment pipeline (Standard / Premium). */
export const LONG_VIDEO_THRESHOLD_SECONDS = VIDEO_SEGMENT_SECONDS;

export type SegmentPlan = {
  segments: number[];
  segmentCount: number;
  totalSeconds: number;
};

export function computeSegmentPlan(
  totalSeconds: number,
  segmentSize = VIDEO_SEGMENT_SECONDS
): SegmentPlan {
  const segments: number[] = [];
  let remaining = Math.max(1, Math.round(totalSeconds));
  while (remaining > 0) {
    segments.push(Math.min(segmentSize, remaining));
    remaining -= segmentSize;
  }
  return {
    segments,
    segmentCount: segments.length,
    totalSeconds: segments.reduce((a, b) => a + b, 0),
  };
}

export function shouldUseLongVideoPipeline(
  tier: "free" | "tester" | "standard" | "premium",
  totalSeconds: number
): boolean {
  return (
    (tier === "standard" || tier === "premium") &&
    totalSeconds > LONG_VIDEO_THRESHOLD_SECONDS
  );
}

export function buildSegmentDirectionPrompt(
  baseDirection: string,
  segmentIndex: number,
  totalSegments: number,
  segmentDuration: number,
  totalDuration: number
): string {
  const startSec = segmentsStartSecond(segmentIndex);
  const endSec = startSec + segmentDuration;
  const header = `[Part ${segmentIndex + 1}/${totalSegments} — seconds ${startSec + 1}-${endSec} of ${totalDuration}]`;
  const continuity =
    segmentIndex === 0
      ? "Opening segment — establish scene, characters, and tone."
      : "Continue seamlessly from the previous segment — same characters, wardrobe, lighting, and story beat.";
  const trimmed = baseDirection.trim();
  return trimmed
    ? `${header}\n${continuity}\n\n${trimmed}`
    : `${header}\n${continuity}`;
}

function segmentsStartSecond(segmentIndex: number): number {
  return segmentIndex * VIDEO_SEGMENT_SECONDS;
}

export function estimateProcessingWindow(
  totalSeconds: number,
  options?: { simulationMode?: boolean; segmentCount?: number }
): { minMinutes: number; maxMinutes: number; segmentCount: number } {
  const segmentCount =
    options?.segmentCount ?? computeSegmentPlan(totalSeconds).segmentCount;
  const perSegmentMin = options?.simulationMode ? 0.5 : 2;
  const perSegmentMax = options?.simulationMode ? 1.5 : 5;
  const stitchMinutes = totalSeconds > LONG_VIDEO_THRESHOLD_SECONDS ? 2 : 0;
  return {
    segmentCount,
    minMinutes: Math.max(1, Math.ceil(segmentCount * perSegmentMin + stitchMinutes)),
    maxMinutes: Math.max(2, Math.ceil(segmentCount * perSegmentMax + stitchMinutes + 1)),
  };
}

export function filenameFromVideoUrl(videoUrl: string): string | null {
  try {
    const path = videoUrl.includes("://")
      ? new URL(videoUrl, "http://local").pathname
      : videoUrl;
    const name = path.split("/").pop();
    return name && name.endsWith(".mp4") ? name : null;
  } catch {
    const name = videoUrl.split("/").pop();
    return name && name.endsWith(".mp4") ? name : null;
  }
}

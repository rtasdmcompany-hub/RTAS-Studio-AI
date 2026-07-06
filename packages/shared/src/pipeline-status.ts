/** Long-render pipeline states persisted on GenerationJob rows. */
export const PIPELINE_STATUSES = [
  "queued",
  "generating_chunks",
  "compiling_media",
  "completed",
  "failed",
] as const;

export type PipelineStatus = (typeof PIPELINE_STATUSES)[number];

export type ChunkManifestEntry = {
  index: number;
  durationSec: number;
  status: "pending" | "generating" | "completed" | "failed";
  falUrl?: string;
  localPath?: string;
  error?: string;
};

export function pipelineStatusLabel(status: PipelineStatus): string {
  switch (status) {
    case "queued":
      return "Queued for GPU worker";
    case "generating_chunks":
      return "Generating 15-second segments";
    case "compiling_media":
      return "Stitching final master";
    case "completed":
      return "Render complete";
    case "failed":
      return "Render failed";
    default:
      return "Processing";
  }
}

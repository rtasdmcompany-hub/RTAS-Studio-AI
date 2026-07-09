export type PipelineStatus =
  | "queued"
  | "processing"
  | "stitching"
  | "ready"
  | "failed";

export type ActivePipelineStatus = "queued" | "processing" | "stitching";

export type ChunkManifestEntry = {
  index: number;
  durationSeconds: number;
  status: PipelineStatus;
  videoUrl?: string;
};

export type UserVideoAsset = {
  id: string;
  userId: string;
  title: string;
  category: import("./domain").VideoCategory;
  mode: import("./domain").GenerationMode;
  visualStyle: import("./domain").VisualStyle;
  durationSeconds: number;
  creditsUsed: number;
  status: PipelineStatus;
  pipelineStatus: PipelineStatus;
  videoUrl?: string | null;
  thumbnailUrl?: string | null;
  simulationMode?: boolean;
  creativePrompt?: string | null;
  isPublic?: boolean;
  createdAt: string;
  updatedAt?: string;
  chunkCount?: number;
  completedChunks?: number;
};

export type Platform =
  | "YOUTUBE"
  | "TIKTOK"
  | "INSTAGRAM"
  | "FACEBOOK"
  | "X"
  | "LINKEDIN";

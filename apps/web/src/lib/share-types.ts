export type PublicSharePayload = {
  id: string;
  title: string;
  prompt: string | null;
  videoUrl: string;
  durationSeconds: number;
  category: string;
  visualStyle: string;
  mode: string;
  isPublic: boolean;
  publishedAt: string;
};

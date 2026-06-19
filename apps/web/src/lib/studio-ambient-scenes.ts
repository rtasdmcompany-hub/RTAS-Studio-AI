/** Maps wizard / preview screens to distinct hero video clips (rotates LANDING_HERO_VIDEO_SOURCES). */
const SCENE_VIDEO_OFFSET: Record<string, number> = {
  setup: 0,
  "title-direction": 1,
  "lyrics-style": 2,
  "duration-prompt": 3,
  duration: 3,
  prompt: 4,
  audio: 4,
  images: 5,
  "face-upload": 6,
  "face-lock": 7,
  preview: 2,
  rendering: 1,
  default: 0,
};

export function getStudioAmbientVideoIndex(scene: string): number {
  return SCENE_VIDEO_OFFSET[scene] ?? SCENE_VIDEO_OFFSET.default;
}

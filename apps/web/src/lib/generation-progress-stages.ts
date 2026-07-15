/**

 * Premium generation progress copy — display only.

 * Shared by pipeline panel, overlay, and progress simulation.

 * Labels map from existing percent bands (no new backend signals).

 */



export type GenerationProgressStage = {

  id: string;

  /** Live status message shown during this band */

  label: string;

  /** Compact checklist / chip label */

  shortLabel: string;

  min: number;

  max: number;

};



export const GENERATION_PROGRESS_STAGES: GenerationProgressStage[] = [

  {

    id: "prepare-assets",

    label: "Preparing Assets...",

    shortLabel: "Preparing Assets",

    min: 0,

    max: 7,

  },

  {

    id: "upload",

    label: "Uploading...",

    shortLabel: "Uploading",

    min: 8,

    max: 15,

  },

  {

    id: "prompt-analysis",

    label: "Prompt Analysis...",

    shortLabel: "Prompt Analysis",

    min: 16,

    max: 24,

  },

  {

    id: "storyboard",

    label: "Storyboard...",

    shortLabel: "Storyboard",

    min: 25,

    max: 33,

  },

  {

    id: "scene-planning",

    label: "Scene Planning...",

    shortLabel: "Scene Planning",

    min: 34,

    max: 42,

  },

  {

    id: "rendering",

    label: "Rendering...",

    shortLabel: "Rendering",

    min: 43,

    max: 60,

  },

  {

    id: "upscaling",

    label: "Upscaling...",

    shortLabel: "Upscaling",

    min: 61,

    max: 70,

  },

  {

    id: "audio-sync",

    label: "Audio Sync...",

    shortLabel: "Audio Sync",

    min: 71,

    max: 78,

  },

  {

    id: "encoding",

    label: "Encoding...",

    shortLabel: "Encoding",

    min: 79,

    max: 87,

  },

  {

    id: "finalizing",

    label: "Finalizing...",

    shortLabel: "Finalizing",

    min: 88,

    max: 98,

  },

  {

    id: "preview-ready",

    label: "Preview Ready",

    shortLabel: "Preview Ready",

    min: 99,

    max: 100,

  },

];



export const GENERATION_LAST_STAGE_INDEX = GENERATION_PROGRESS_STAGES.length - 1;



export function stageIndexFromPercent(percent: number): number {

  const p = Math.min(100, Math.max(0, percent));

  if (p >= 100) return GENERATION_LAST_STAGE_INDEX;

  for (let i = 0; i < GENERATION_PROGRESS_STAGES.length; i++) {

    const stage = GENERATION_PROGRESS_STAGES[i];

    if (p >= stage.min && p <= stage.max) return i;

  }

  return 0;

}



export function messageForPercent(percent: number): string {

  return GENERATION_PROGRESS_STAGES[stageIndexFromPercent(percent)].label;

}



export function isProgressStageDone(index: number, percent: number): boolean {

  const stage = GENERATION_PROGRESS_STAGES[index];

  if (!stage) return false;

  if (percent >= 100) return true;

  return percent > stage.max;

}



/** High-level rail (4 steps) mapped from percent — keeps the top stepper calm. */

export function pipelineRailIndexFromPercent(percent: number): number {

  if (percent < 16) return 0; // Assets: prepare + upload

  if (percent < 43) return 1; // Plan: analysis → scene planning

  if (percent < 88) return 2; // Render: rendering → encoding

  return 3; // Deliver: finalizing → preview ready

}



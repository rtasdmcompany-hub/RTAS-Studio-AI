import type { GenerationMode, VideoCategory, VisualStyle } from "@rtas/shared";

const PROMPT_HISTORY_KEY = "rtas_prompt_history";
const FAVORITE_PROMPTS_KEY = "rtas_favorite_prompts";
const WORKFLOWS_KEY = "rtas_saved_workflows";
const RECENT_PROJECTS_KEY = "rtas_recent_projects";

const MAX_PROMPT_HISTORY = 24;
const MAX_RECENT_PROJECTS = 12;
const MAX_WORKFLOWS = 20;

export type SavedWorkflow = {
  id: string;
  name: string;
  savedAt: string;
  mode: GenerationMode;
  category: VideoCategory | null;
  visualStyle: VisualStyle;
  text: Record<string, string>;
};

export type RecentProject = {
  id: string;
  title: string;
  prompt?: string;
  category?: string;
  durationSeconds?: number;
  createdAt: string;
  status: "ready" | "processing" | "failed";
};

function readJson<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function writeJson(key: string, value: unknown): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* quota */
  }
}

export function loadPromptHistory(): string[] {
  const items = readJson<string[]>(PROMPT_HISTORY_KEY, []);
  return items.filter((p) => typeof p === "string" && p.trim().length > 0);
}

export function addPromptToHistory(prompt: string): void {
  const trimmed = prompt.trim();
  if (!trimmed || trimmed.length < 8) return;
  const existing = loadPromptHistory().filter((p) => p !== trimmed);
  writeJson(PROMPT_HISTORY_KEY, [trimmed, ...existing].slice(0, MAX_PROMPT_HISTORY));
}

export function loadFavoritePrompts(): string[] {
  return readJson<string[]>(FAVORITE_PROMPTS_KEY, []).filter(Boolean);
}

export function isFavoritePrompt(prompt: string): boolean {
  return loadFavoritePrompts().includes(prompt.trim());
}

export function toggleFavoritePrompt(prompt: string): boolean {
  const trimmed = prompt.trim();
  if (!trimmed) return false;
  const favorites = loadFavoritePrompts();
  const exists = favorites.includes(trimmed);
  const next = exists
    ? favorites.filter((p) => p !== trimmed)
    : [trimmed, ...favorites].slice(0, MAX_PROMPT_HISTORY);
  writeJson(FAVORITE_PROMPTS_KEY, next);
  return !exists;
}

export function loadSavedWorkflows(): SavedWorkflow[] {
  return readJson<SavedWorkflow[]>(WORKFLOWS_KEY, []).filter(
    (w) => w && typeof w.name === "string" && w.id
  );
}

export function saveWorkflow(
  name: string,
  snapshot: Omit<SavedWorkflow, "id" | "savedAt" | "name">
): SavedWorkflow {
  const workflow: SavedWorkflow = {
    id: `wf-${Date.now()}`,
    name: name.trim() || "Untitled workflow",
    savedAt: new Date().toISOString(),
    ...snapshot,
  };
  const existing = loadSavedWorkflows().filter((w) => w.name !== workflow.name);
  writeJson(WORKFLOWS_KEY, [workflow, ...existing].slice(0, MAX_WORKFLOWS));
  return workflow;
}

export function deleteSavedWorkflow(id: string): void {
  writeJson(
    WORKFLOWS_KEY,
    loadSavedWorkflows().filter((w) => w.id !== id)
  );
}

export function loadRecentProjects(): RecentProject[] {
  return readJson<RecentProject[]>(RECENT_PROJECTS_KEY, []);
}

export function upsertRecentProject(project: RecentProject): void {
  const existing = loadRecentProjects().filter((p) => p.id !== project.id);
  writeJson(RECENT_PROJECTS_KEY, [project, ...existing].slice(0, MAX_RECENT_PROJECTS));
}

export function removeRecentProject(id: string): void {
  writeJson(
    RECENT_PROJECTS_KEY,
    loadRecentProjects().filter((p) => p.id !== id)
  );
}

import {
  CATEGORY_META,
  type GenerationMode,
  type VideoCategory,
  type VisualStyle,
} from "@rtas/shared";

const DRAFT_KEY = "rtas_studio_draft";
const FIELD_HISTORY_KEY = "rtas_studio_field_history";
const BACKUP_VERSION = 1;

export type StudioDraftSnapshot = {
  version: typeof BACKUP_VERSION;
  savedAt: string;
  mode: GenerationMode;
  category: VideoCategory | null;
  visualStyle: VisualStyle;
  text: Record<string, string>;
};

export type FieldHistory = Record<string, string>;

const VALID_CATEGORIES = new Set(Object.keys(CATEGORY_META));
const VALID_MODES = new Set<GenerationMode>(["prompt", "image"]);
const VALID_STYLES = new Set<VisualStyle>(["real", "avatar", "cartoon"]);

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function sanitizeText(raw: unknown): Record<string, string> {
  if (!isObject(raw)) return { duration: "30" };
  const text: Record<string, string> = {};
  for (const [key, value] of Object.entries(raw)) {
    if (typeof value === "string") text[key] = value;
  }
  if (!text.duration) text.duration = "30";
  return text;
}

function parseDraft(raw: unknown): StudioDraftSnapshot | null {
  if (!isObject(raw)) return null;
  if (raw.version !== BACKUP_VERSION) return null;

  const mode = raw.mode;
  const visualStyle = raw.visualStyle;
  if (typeof mode !== "string" || !VALID_MODES.has(mode as GenerationMode)) {
    return null;
  }
  if (
    typeof visualStyle !== "string" ||
    !VALID_STYLES.has(visualStyle as VisualStyle)
  ) {
    return null;
  }

  let category: VideoCategory | null = null;
  if (raw.category != null) {
    if (typeof raw.category !== "string" || !VALID_CATEGORIES.has(raw.category)) {
      return null;
    }
    category = raw.category as VideoCategory;
  }

  return {
    version: BACKUP_VERSION,
    savedAt: typeof raw.savedAt === "string" ? raw.savedAt : new Date().toISOString(),
    mode: mode as GenerationMode,
    category,
    visualStyle: visualStyle as VisualStyle,
    text: sanitizeText(raw.text),
  };
}

export function loadStudioDraft(): StudioDraftSnapshot | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(DRAFT_KEY);
    if (!raw) return null;
    return parseDraft(JSON.parse(raw));
  } catch {
    return null;
  }
}

export function clearStudioDraft(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(DRAFT_KEY);
  } catch {
    /* ignore */
  }
}

let draftSaveSuppressed = false;

/** Pause draft writes while the studio form resets after generation. */
export function suppressStudioDraftSave(): void {
  draftSaveSuppressed = true;
  clearStudioDraft();
}

export function resumeStudioDraftSave(): void {
  draftSaveSuppressed = false;
}

export function isStudioDraftSaveSuppressed(): boolean {
  return draftSaveSuppressed;
}

export function saveStudioDraft(snapshot: Omit<StudioDraftSnapshot, "version" | "savedAt">): void {
  if (typeof window === "undefined") return;
  if (draftSaveSuppressed) return;
  const payload: StudioDraftSnapshot = {
    version: BACKUP_VERSION,
    savedAt: new Date().toISOString(),
    mode: snapshot.mode,
    category: snapshot.category,
    visualStyle: snapshot.visualStyle,
    text: snapshot.text,
  };
  try {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(payload));
  } catch {
    /* quota or private mode */
  }
}

export function loadFieldHistory(): FieldHistory {
  if (typeof window === "undefined") return {};
  try {
    const raw = localStorage.getItem(FIELD_HISTORY_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    if (!isObject(parsed)) return {};
    const history: FieldHistory = {};
    for (const [key, value] of Object.entries(parsed)) {
      if (typeof value === "string" && value.trim()) history[key] = value;
    }
    return history;
  } catch {
    return {};
  }
}

export function saveFieldHistory(history: FieldHistory): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(FIELD_HISTORY_KEY, JSON.stringify(history));
  } catch {
    /* ignore */
  }
}

/** Remember the last non-empty value typed into a field. */
export function rememberFieldValue(fieldId: string, value: string): void {
  const trimmed = value.trim();
  if (!trimmed) return;
  const history = loadFieldHistory();
  history[fieldId] = value;
  saveFieldHistory(history);
}

export function getFieldLastValue(fieldId: string): string | null {
  const value = loadFieldHistory()[fieldId];
  return value?.trim() ? value : null;
}

export function draftHasRestorableContent(draft: StudioDraftSnapshot | null): boolean {
  if (!draft) return false;
  const hasText = Object.entries(draft.text).some(
    ([key, value]) =>
      key !== "duration" && key !== "videoTitle" && value.trim().length > 0
  );
  const hasTitle = Boolean(draft.text.videoTitle?.trim());
  return Boolean(draft.category) || hasText || hasTitle || draft.text.duration !== "30";
}

export function draftDiffersFrom(
  draft: StudioDraftSnapshot,
  mode: GenerationMode,
  category: VideoCategory | null,
  visualStyle: VisualStyle,
  text: Record<string, string>
): boolean {
  if (draft.mode !== mode) return true;
  if (draft.category !== category) return true;
  if (draft.visualStyle !== visualStyle) return true;

  const keys = new Set([...Object.keys(draft.text), ...Object.keys(text)]);
  for (const key of keys) {
    if ((draft.text[key] ?? "") !== (text[key] ?? "")) return true;
  }
  return false;
}

export function seedFieldHistoryFromText(text: Record<string, string>): void {
  const history = loadFieldHistory();
  let changed = false;
  for (const [fieldId, value] of Object.entries(text)) {
    if (!value.trim()) continue;
    if (history[fieldId] !== value) {
      history[fieldId] = value;
      changed = true;
    }
  }
  if (changed) saveFieldHistory(history);
}

export function truncatePreview(value: string, max = 72): string {
  const single = value.replace(/\s+/g, " ").trim();
  if (single.length <= max) return single;
  return `${single.slice(0, max - 1)}…`;
}

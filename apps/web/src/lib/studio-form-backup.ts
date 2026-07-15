import {
  CATEGORY_META,
  type GenerationMode,
  type VideoCategory,
  type VisualStyle,
} from "@rtas/shared";

const DRAFT_KEY = "rtas_studio_draft";
export const DRAFTS_LIST_KEY = "rtas_studio_drafts_v1";
const FIELD_HISTORY_KEY = "rtas_studio_field_history";
const BACKUP_VERSION = 1;
const CURRENT_DRAFT_ID = "current";

export type StudioDraftSnapshot = {
  version: typeof BACKUP_VERSION;
  savedAt: string;
  mode: GenerationMode;
  category: VideoCategory | null;
  visualStyle: VisualStyle;
  text: Record<string, string>;
};

export type StudioDraftListItem = {
  id: string;
  name: string;
  savedAt: string;
  snapshot: StudioDraftSnapshot;
  thumbnail?: string;
  categoryLabel?: string;
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

function draftDisplayName(snapshot: StudioDraftSnapshot, fallback = "Current draft"): string {
  const title = snapshot.text.videoTitle?.trim();
  if (title) return title;
  const prompt =
    snapshot.text.directionPrompt?.trim() ||
    snapshot.text.mainPrompt?.trim() ||
    snapshot.text.prompt?.trim();
  if (prompt) return truncatePreview(prompt, 48);
  return fallback;
}

function categoryLabelFor(category: VideoCategory | null): string | undefined {
  if (!category) return undefined;
  return CATEGORY_META[category]?.shortLabel ?? CATEGORY_META[category]?.label;
}

function createDraftId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `draft_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

function parseDraftListItem(raw: unknown): StudioDraftListItem | null {
  if (!isObject(raw)) return null;
  if (typeof raw.id !== "string" || !raw.id.trim()) return null;
  if (typeof raw.name !== "string") return null;
  const snapshot = parseDraft(raw.snapshot);
  if (!snapshot) return null;
  return {
    id: raw.id,
    name: raw.name.trim() || draftDisplayName(snapshot, "Untitled draft"),
    savedAt:
      typeof raw.savedAt === "string" ? raw.savedAt : snapshot.savedAt,
    snapshot,
    thumbnail: typeof raw.thumbnail === "string" ? raw.thumbnail : undefined,
    categoryLabel:
      typeof raw.categoryLabel === "string"
        ? raw.categoryLabel
        : categoryLabelFor(snapshot.category),
  };
}

function readDraftsList(): StudioDraftListItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(DRAFTS_LIST_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed
      .map(parseDraftListItem)
      .filter((item): item is StudioDraftListItem => item != null);
  } catch {
    return [];
  }
}

function writeDraftsList(items: StudioDraftListItem[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(DRAFTS_LIST_KEY, JSON.stringify(items));
  } catch {
    /* quota or private mode */
  }
}

function upsertDraftListItem(item: StudioDraftListItem): StudioDraftListItem {
  const list = readDraftsList().filter((d) => d.id !== item.id);
  list.unshift(item);
  writeDraftsList(list);
  return item;
}

export function listStudioDrafts(): StudioDraftListItem[] {
  return readDraftsList().sort(
    (a, b) => new Date(b.savedAt).getTime() - new Date(a.savedAt).getTime()
  );
}

export function loadDraftById(id: string): StudioDraftListItem | null {
  return readDraftsList().find((d) => d.id === id) ?? null;
}

export function searchDrafts(query: string): StudioDraftListItem[] {
  const q = query.trim().toLowerCase();
  const drafts = listStudioDrafts();
  if (!q) return drafts;
  return drafts.filter((d) => {
    const haystack = [
      d.name,
      d.categoryLabel ?? "",
      d.snapshot.text.videoTitle ?? "",
      d.snapshot.text.directionPrompt ?? "",
      d.snapshot.text.mainPrompt ?? "",
      d.snapshot.category ?? "",
      d.snapshot.mode,
      d.snapshot.visualStyle,
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(q);
  });
}

export function saveNamedDraft(name?: string): StudioDraftListItem | null {
  const current = loadStudioDraft();
  if (!current || !draftHasRestorableContent(current)) return null;
  const savedAt = new Date().toISOString();
  const snapshot: StudioDraftSnapshot = { ...current, savedAt };
  const item: StudioDraftListItem = {
    id: createDraftId(),
    name: (name?.trim() || draftDisplayName(snapshot, "Untitled draft")).trim(),
    savedAt,
    snapshot,
    categoryLabel: categoryLabelFor(snapshot.category),
  };
  return upsertDraftListItem(item);
}

export function renameDraft(id: string, name: string): StudioDraftListItem | null {
  const trimmed = name.trim();
  if (!trimmed) return null;
  const list = readDraftsList();
  const idx = list.findIndex((d) => d.id === id);
  if (idx < 0) return null;
  const updated: StudioDraftListItem = { ...list[idx], name: trimmed };
  list[idx] = updated;
  writeDraftsList(list);
  return updated;
}

export function duplicateDraft(id: string): StudioDraftListItem | null {
  const source = loadDraftById(id);
  if (!source) return null;
  const savedAt = new Date().toISOString();
  const item: StudioDraftListItem = {
    id: createDraftId(),
    name: `${source.name} (copy)`,
    savedAt,
    snapshot: { ...source.snapshot, savedAt },
    thumbnail: source.thumbnail,
    categoryLabel: source.categoryLabel ?? categoryLabelFor(source.snapshot.category),
  };
  return upsertDraftListItem(item);
}

export function deleteDraft(id: string): boolean {
  const list = readDraftsList();
  const next = list.filter((d) => d.id !== id);
  if (next.length === list.length) return false;
  writeDraftsList(next);
  if (id === CURRENT_DRAFT_ID) {
    clearStudioDraft();
  }
  return true;
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
    if (draftHasRestorableContent(payload)) {
      upsertDraftListItem({
        id: CURRENT_DRAFT_ID,
        name: draftDisplayName(payload, "Current draft"),
        savedAt: payload.savedAt,
        snapshot: payload,
        categoryLabel: categoryLabelFor(payload.category),
      });
    }
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

import {
  CATEGORY_META,
  DURATION_FIELD,
  getVisibleFieldIds,
  getVisibleFields,
  identityPipelineForVisualStyle,
  type CategoryField,
  type IdentityPipelineConfig,
  type GenerationMode,
  type VideoCategory,
  type VisualStyle,
} from "@rtas/shared";

export type FileFieldValue = {
  file: File;
  name: string;
  mimeType: string;
  size: number;
};

/** User-defined list / player title (always preserved across category changes). */
export const VIDEO_TITLE_FIELD_ID = "videoTitle";

export const WIZARD_SETUP_STEP = 0;
export const WIZARD_FIRST_GROUP_STEP = 1;

export const VIDEO_TITLE_FIELD: CategoryField = {
  id: VIDEO_TITLE_FIELD_ID,
  label: "Video Title",
  shortLabel: "Title",
  type: "text",
  required: true,
  placeholder: "Name shown in Your videos list",
  helpText: "This exact name appears in Your videos and the preview player.",
};

export type WizardStepGroup = {
  id: string;
  label: string;
  fields: CategoryField[];
};

/** Grouped wizard pages — multiple related inputs per step. */
export function getWizardStepGroups(
  category: VideoCategory,
  mode: GenerationMode,
  visualStyle: VisualStyle
): WizardStepGroup[] {
  const detailFields = [DURATION_FIELD, ...getVisibleFields(category, mode, visualStyle)];
  const fieldMap = new Map<string, CategoryField>();
  fieldMap.set(VIDEO_TITLE_FIELD_ID, VIDEO_TITLE_FIELD);
  for (const field of detailFields) {
    fieldMap.set(field.id, field);
  }

  const groups: WizardStepGroup[] = [];
  const used = new Set<string>();

  const addGroup = (
    id: string,
    label: string,
    ids: string[],
    options?: { allowEmpty?: boolean }
  ) => {
    const fields = ids
      .filter((fieldId) => fieldMap.has(fieldId) && !used.has(fieldId))
      .map((fieldId) => fieldMap.get(fieldId)!);
    if (fields.length === 0 && !options?.allowEmpty) return;
    for (const field of fields) used.add(field.id);
    groups.push({ id, label, fields });
  };

  /* Guided editor flow: Character → Product → Voice → Prompt → Advanced */
  if (visualStyle === "real") {
    addGroup("face-upload", "Upload character", ["faceReference", "faceConsent"]);
    addGroup("face-lock", "Identity lock", [], { allowEmpty: true });
  }

  addGroup("images", "Upload product", [
    "sourceImage",
    "referenceImage",
    "productImage",
    "coverImage",
  ]);
  addGroup("audio", "Upload voice", ["audioSource"]);
  addGroup("title-direction", "Prompt", ["directionPrompt", "mainPrompt"]);
  addGroup("lyrics-style", "Lyrics & music style", ["lyrics", "musicStyle"]);
  addGroup("duration-prompt", "Advanced settings", ["duration"]);

  for (const field of detailFields) {
    if (!used.has(field.id)) {
      addGroup(field.id, field.shortLabel || field.label, [field.id]);
    }
  }

  return groups;
}

export function getWizardStepCount(
  category: VideoCategory | null,
  mode: GenerationMode | null,
  visualStyle: VisualStyle | null
): number {
  if (!category || !mode || !visualStyle) return 1;
  return WIZARD_FIRST_GROUP_STEP + getWizardStepGroups(category, mode, visualStyle).length;
}

export function getWizardGroupAtStep(
  wizardStep: number,
  category: VideoCategory | null,
  mode: GenerationMode | null,
  visualStyle: VisualStyle | null
): WizardStepGroup | null {
  if (!category || !mode || !visualStyle || wizardStep < WIZARD_FIRST_GROUP_STEP) {
    return null;
  }
  const groups = getWizardStepGroups(category, mode, visualStyle);
  return groups[wizardStep - WIZARD_FIRST_GROUP_STEP] ?? null;
}

export function isWizardFieldRequired(
  field: CategoryField,
  visualStyle: VisualStyle
): boolean {
  if (field.required) return true;
  if (visualStyle === "real" && (field.id === "faceConsent" || field.id === "faceReference")) {
    return true;
  }
  return false;
}

export function validateWizardField(
  fieldId: string,
  category: VideoCategory,
  mode: GenerationMode,
  visualStyle: VisualStyle,
  state: StudioFormState
): FieldValidationError | null {
  const errors = collectRequiredFieldErrors(category, mode, visualStyle, state);
  return errors.find((e) => e.fieldId === fieldId) ?? null;
}

export function validateWizardGroup(
  group: WizardStepGroup,
  category: VideoCategory,
  mode: GenerationMode,
  visualStyle: VisualStyle,
  state: StudioFormState
): FieldValidationError[] {
  const errors: FieldValidationError[] = [];
  for (const field of group.fields) {
    if (!isWizardFieldRequired(field, visualStyle)) continue;
    const err = validateWizardField(field.id, category, mode, visualStyle, state);
    if (err) errors.push(err);
  }
  return errors;
}

export interface StudioFormState {
  text: Record<string, string>;
  files: Record<string, FileFieldValue | null>;
  identityPipeline: IdentityPipelineConfig;
}

export function createInitialFormState(): StudioFormState {
  return {
    text: { [VIDEO_TITLE_FIELD_ID]: "" },
    files: {},
    identityPipeline: identityPipelineForVisualStyle("avatar"),
  };
}

export function syncIdentityPipeline(
  state: StudioFormState,
  visualStyle: VisualStyle
): StudioFormState {
  return {
    ...state,
    identityPipeline: identityPipelineForVisualStyle(visualStyle),
  };
}

/** Drop values for fields that are no longer visible */
export function pruneFormToVisible(
  state: StudioFormState,
  category: VideoCategory,
  mode: GenerationMode,
  visualStyle: VisualStyle
): StudioFormState {
  const visible = new Set([
    DURATION_FIELD.id,
    ...getVisibleFieldIds(category, mode, visualStyle),
  ]);

  const text: Record<string, string> = {};
  if (state.text[VIDEO_TITLE_FIELD_ID] !== undefined) {
    text[VIDEO_TITLE_FIELD_ID] = state.text[VIDEO_TITLE_FIELD_ID];
  }
  for (const id of visible) {
    if (state.text[id] !== undefined) text[id] = state.text[id];
  }
  if (!text.duration) text.duration = "15";

  const files: Record<string, FileFieldValue | null> = {};
  for (const id of visible) {
    if (state.files[id]) files[id] = state.files[id];
  }

  return {
    text,
    files,
    identityPipeline: identityPipelineForVisualStyle(visualStyle),
  };
}

/** Payload for Generate API (files as metadata until upload service exists) */
export function buildGeneratePayload(
  state: StudioFormState,
  category: VideoCategory,
  mode: GenerationMode,
  visualStyle: VisualStyle
) {
  const fileMeta: Record<string, { name: string; mimeType: string; size: number }> =
    {};
  for (const [id, v] of Object.entries(state.files)) {
    if (v) fileMeta[id] = { name: v.name, mimeType: v.mimeType, size: v.size };
  }

  const durationRaw = Number.parseInt(String(state.text.duration ?? "").trim(), 10);
  const durationSeconds =
    Number.isFinite(durationRaw) && durationRaw > 0 ? durationRaw : undefined;

  return {
    fields: { ...state.text },
    files: fileMeta,
    identityPipeline: state.identityPipeline,
    category,
    mode,
    visualStyle,
    ...(durationSeconds !== undefined ? { durationSeconds } : {}),
  };
}

export const FIELD_REQUIRED_MESSAGE =
  "This field is required to generate your cinematic video.";

export type FieldValidationError = {
  fieldId: string;
  message: string;
};

export function collectRequiredFieldErrors(
  category: VideoCategory,
  mode: GenerationMode,
  visualStyle: VisualStyle,
  state: StudioFormState
): FieldValidationError[] {
  const errors: FieldValidationError[] = [];
  const push = (fieldId: string, message = FIELD_REQUIRED_MESSAGE) => {
    if (errors.some((e) => e.fieldId === fieldId)) return;
    errors.push({ fieldId, message });
  };

  if (!state.text[VIDEO_TITLE_FIELD_ID]?.trim()) {
    push(VIDEO_TITLE_FIELD_ID);
  }

  const fields = [
    DURATION_FIELD,
    ...getVisibleFields(category, mode, visualStyle),
  ];

  for (const f of fields) {
    if (!f.required) continue;
    if (f.type === "file") {
      if (!state.files[f.id]) push(f.id);
    } else if (!state.text[f.id]?.trim()) {
      push(f.id);
    }
  }

  if (visualStyle === "real") {
    const consent = state.text.faceConsent?.trim().toUpperCase();
    if (consent !== "YES") {
      const consentMessage = consent
        ? 'Type exactly "YES" to confirm you have rights to use this face.'
        : "Type YES in the consent box above, then click Generate again.";
      const existing = errors.find((e) => e.fieldId === "faceConsent");
      if (existing) existing.message = consentMessage;
      else push("faceConsent", consentMessage);
    }
    if (!state.files.faceReference) push("faceReference");
  }

  return errors;
}

const FIELD_LABEL_OVERRIDES: Record<string, string> = {
  videoTitle: "Video Title",
  directionPrompt: "Directional Prompt",
  mainPrompt: "Visual Scene Description",
  faceConsent: "Face consent — type YES",
  faceReference: "Face Photo",
  sourceImage: "Source Image",
  duration: "Video Length",
};

/** Customer-friendly list of missing required fields. */
export function buildMissingFieldsMessage(
  errors: FieldValidationError[],
  category: VideoCategory,
  mode: GenerationMode,
  visualStyle: VisualStyle
): string {
  const labelMap = new Map<string, string>();
  for (const f of [DURATION_FIELD, ...getVisibleFields(category, mode, visualStyle)]) {
    labelMap.set(f.id, f.shortLabel || f.label);
  }
  for (const [id, label] of Object.entries(FIELD_LABEL_OVERRIDES)) {
    labelMap.set(id, label);
  }

  const labels = errors.map(
    (e) => labelMap.get(e.fieldId) ?? e.fieldId
  );
  const unique = [...new Set(labels)];
  return `Please complete these fields first: ${unique.join(", ")}.`;
}

export function scrollToFirstFieldError(fieldId: string): void {
  if (typeof document === "undefined") return;
  const el = document.getElementById(fieldId);
  if (!el) return;
  const scrollTarget =
    el.closest<HTMLElement>(".field, .file-upload, .field--video-title") ?? el;
  scrollTarget.scrollIntoView({ behavior: "smooth", block: "center" });
  if (
    el instanceof HTMLInputElement ||
    el instanceof HTMLTextAreaElement ||
    el instanceof HTMLSelectElement
  ) {
    if (el.type !== "file") {
      el.focus({ preventScroll: true });
    }
  }
}

export const DURATION_PROMPT_GROUP_ID = "duration-prompt";

/** Earlier wizard text used to pre-fill Visual Scene Description when empty. */
const VISUAL_SCENE_SOURCE_FIELD_IDS = [
  "directionPrompt",
  "lyrics",
  "script",
  "adScript",
  "story",
  "plot",
  "talkingPoints",
  "topic",
] as const;

export function buildVisualSceneAutoFill(state: StudioFormState): string {
  const t = state.text;
  for (const fieldId of VISUAL_SCENE_SOURCE_FIELD_IDS) {
    const value = t[fieldId]?.trim();
    if (value) return value;
  }
  return "";
}

export function extractCreativePrompt(state: StudioFormState): string {
  const t = state.text;
  return (
    t.directionPrompt?.trim() ||
    t.prompt?.trim() ||
    t.mainPrompt?.trim() ||
    t.lyrics?.trim()?.slice(0, 280) ||
    ""
  );
}

export function validateRequiredFields(
  category: VideoCategory,
  mode: GenerationMode,
  visualStyle: VisualStyle,
  state: StudioFormState
): string | null {
  const errors = collectRequiredFieldErrors(category, mode, visualStyle, state);
  return errors.length > 0 ? errors[0].message : null;
}

/** Title shown in Your videos list and preview player — always the Video Title field. */
export function buildVideoTitle(
  _category: VideoCategory,
  _mode: GenerationMode,
  state: StudioFormState
): string {
  return state.text[VIDEO_TITLE_FIELD_ID]?.trim() || "Untitled video";
}

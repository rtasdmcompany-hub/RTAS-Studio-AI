import { CATEGORY_FIELDS, IMAGE_MODE_FIELDS, PROMPT_MODE_FIELDS, REAL_FACE_FIELDS } from "./categories";
import type { CategoryField, GenerationMode, VideoCategory, VisualStyle } from "./types";

const DURATION_ID = "duration";

/** Field ids shown for the active category + mode + visual style only */
export function getVisibleFieldIds(
  category: VideoCategory,
  mode: GenerationMode,
  visualStyle: VisualStyle
): string[] {
  const fields = getVisibleFields(category, mode, visualStyle);
  return fields.map((f) => f.id);
}

export function getVisibleFields(
  category: VideoCategory,
  mode: GenerationMode,
  visualStyle: VisualStyle
): CategoryField[] {
  const modeFields = mode === "image" ? IMAGE_MODE_FIELDS : PROMPT_MODE_FIELDS;
  const categoryFields = CATEGORY_FIELDS[category];
  const realFields = visualStyle === "real" ? REAL_FACE_FIELDS : [];
  return [...modeFields, ...categoryFields, ...realFields];
}

export function isDurationField(id: string): boolean {
  return id === DURATION_ID;
}

export { DURATION_ID };

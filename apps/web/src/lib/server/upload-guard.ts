export const MAX_UPLOAD_BYTES = 52_428_800; // 50 MB

export const ALLOWED_IMAGE_MIMES = new Set([
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/gif",
]);

export const ALLOWED_AUDIO_MIMES = new Set([
  "audio/mpeg",
  "audio/wav",
  "audio/mp4",
  "audio/x-m4a",
  "audio/mpeg3",
]);

export const ALLOWED_UPLOAD_FIELD_IDS = new Set([
  "faceReference",
  "audioSource",
  "audio",
  "referenceImage",
  "sourceImage",
  "productImage",
  "coverImage",
]);

const IMAGE_FIELDS = new Set([
  "faceReference",
  "referenceImage",
  "sourceImage",
  "productImage",
  "coverImage",
]);

const AUDIO_FIELDS = new Set(["audioSource", "audio"]);

const FIELD_ID_RE = /^[a-zA-Z][a-zA-Z0-9_]{0,63}$/;

export class UploadValidationError extends Error {
  constructor(
    message: string,
    readonly status: number
  ) {
    super(message);
    this.name = "UploadValidationError";
  }
}

function validateFieldId(fieldId: string): void {
  if (!ALLOWED_UPLOAD_FIELD_IDS.has(fieldId) || !FIELD_ID_RE.test(fieldId)) {
    throw new UploadValidationError(`Invalid upload field id: ${fieldId}`, 400);
  }
}

function validateFileMeta(fieldId: string, file: File): void {
  validateFieldId(fieldId);

  if (file.size <= 0) {
    throw new UploadValidationError(`Empty file for ${fieldId}`, 400);
  }

  if (file.size > MAX_UPLOAD_BYTES) {
    throw new UploadValidationError(
      `File too large (max ${MAX_UPLOAD_BYTES / (1024 * 1024)} MB)`,
      413
    );
  }

  const contentType = (file.type || "application/octet-stream").toLowerCase();

  if (IMAGE_FIELDS.has(fieldId)) {
    if (!ALLOWED_IMAGE_MIMES.has(contentType)) {
      throw new UploadValidationError(
        `Invalid image type for ${fieldId}: ${contentType}`,
        400
      );
    }
    return;
  }

  if (AUDIO_FIELDS.has(fieldId)) {
    if (!ALLOWED_AUDIO_MIMES.has(contentType)) {
      throw new UploadValidationError(
        `Invalid audio type for ${fieldId}: ${contentType}`,
        400
      );
    }
  }
}

export function validateUploadFormData(formData: FormData): {
  outbound: FormData;
  fileCount: number;
} {
  const outbound = new FormData();
  let fileCount = 0;

  for (const [key, value] of formData.entries()) {
    if (key === "job_id" || key === "jobId") {
      const jobId = String(value).trim();
      if (jobId) outbound.append("job_id", jobId);
      continue;
    }

    if (!(value instanceof File)) continue;

    validateFileMeta(key, value);
    outbound.append(key, value, value.name);
    fileCount += 1;
  }

  if (fileCount === 0) {
    throw new UploadValidationError(
      "No files provided. Attach at least one asset field.",
      400
    );
  }

  return { outbound, fileCount };
}

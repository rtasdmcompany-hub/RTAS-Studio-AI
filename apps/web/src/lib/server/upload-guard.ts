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

function startsWithBytes(buf: Uint8Array, sig: number[]): boolean {
  if (buf.length < sig.length) return false;
  return sig.every((b, i) => buf[i] === b);
}

function looksLikeJpeg(buf: Uint8Array): boolean {
  return startsWithBytes(buf, [0xff, 0xd8, 0xff]);
}

function looksLikePng(buf: Uint8Array): boolean {
  return startsWithBytes(buf, [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
}

function looksLikeGif(buf: Uint8Array): boolean {
  return (
    startsWithBytes(buf, [0x47, 0x49, 0x46, 0x38, 0x37, 0x61]) ||
    startsWithBytes(buf, [0x47, 0x49, 0x46, 0x38, 0x39, 0x61])
  );
}

function looksLikeWebp(buf: Uint8Array): boolean {
  return (
    startsWithBytes(buf, [0x52, 0x49, 0x46, 0x46]) &&
    buf.length >= 12 &&
    buf[8] === 0x57 &&
    buf[9] === 0x45 &&
    buf[10] === 0x42 &&
    buf[11] === 0x50
  );
}

function looksLikeWav(buf: Uint8Array): boolean {
  return (
    startsWithBytes(buf, [0x52, 0x49, 0x46, 0x46]) &&
    buf.length >= 12 &&
    buf[8] === 0x57 &&
    buf[9] === 0x41 &&
    buf[10] === 0x56 &&
    buf[11] === 0x45
  );
}

function looksLikeMp3(buf: Uint8Array): boolean {
  // ID3 tag or MPEG frame sync
  return (
    startsWithBytes(buf, [0x49, 0x44, 0x33]) ||
    (buf.length >= 2 && buf[0] === 0xff && (buf[1] & 0xe0) === 0xe0)
  );
}

function looksLikeMp4Family(buf: Uint8Array): boolean {
  // ftyp box at offset 4
  return (
    buf.length >= 8 &&
    buf[4] === 0x66 &&
    buf[5] === 0x74 &&
    buf[6] === 0x79 &&
    buf[7] === 0x70
  );
}

async function assertMagicBytes(fieldId: string, file: File): Promise<void> {
  const header = new Uint8Array(await file.slice(0, 32).arrayBuffer());

  if (IMAGE_FIELDS.has(fieldId)) {
    const ok =
      looksLikeJpeg(header) ||
      looksLikePng(header) ||
      looksLikeGif(header) ||
      looksLikeWebp(header);
    if (!ok) {
      throw new UploadValidationError(
        `File content does not match an allowed image format for ${fieldId}.`,
        400
      );
    }
    return;
  }

  if (AUDIO_FIELDS.has(fieldId)) {
    const ok =
      looksLikeMp3(header) || looksLikeWav(header) || looksLikeMp4Family(header);
    if (!ok) {
      throw new UploadValidationError(
        `File content does not match an allowed audio format for ${fieldId}.`,
        400
      );
    }
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

export async function validateUploadFormData(formData: FormData): Promise<{
  outbound: FormData;
  fileCount: number;
}> {
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
    await assertMagicBytes(key, value);
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

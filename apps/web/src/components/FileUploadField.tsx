"use client";

import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import type { FileFieldValue } from "@/lib/studio-form";

type UploadKind = "image" | "audio" | "file";

type Props = {
  id: string;
  label: string;
  accept?: string;
  helpText?: string;
  value: FileFieldValue | null;
  onChange: (value: FileFieldValue | null) => void;
  hasError?: boolean;
  errorMessage?: string;
  disabled?: boolean;
};

const IMAGE_FIELDS = new Set([
  "referenceImage",
  "productImage",
  "coverImage",
  "sourceImage",
  "faceReference",
]);

const AUDIO_FIELDS = new Set(["audioSource"]);

function detectKind(id: string, accept?: string): UploadKind {
  if (IMAGE_FIELDS.has(id) || accept?.startsWith("image")) return "image";
  if (AUDIO_FIELDS.has(id) || accept?.startsWith("audio")) return "audio";
  return "file";
}

function kindCopy(kind: UploadKind, id: string): { title: string; hint: string } {
  if (id === "faceReference") {
    return {
      title: "Drop face reference",
      hint: "Clear front-facing photo · PNG/JPG · paste image or URL",
    };
  }
  if (id === "productImage") {
    return {
      title: "Drop product image",
      hint: "Clean product shot on neutral background · PNG/JPG · paste or URL",
    };
  }
  if (id === "sourceImage") {
    return {
      title: "Drop source image",
      hint: "Image to animate · PNG/JPG/WebP · paste or URL",
    };
  }
  if (id === "coverImage") {
    return {
      title: "Drop cover art",
      hint: "Podcast / episode artwork · PNG/JPG · paste or URL",
    };
  }
  if (id === "referenceImage") {
    return {
      title: "Drop reference image",
      hint: "Style or scene reference · PNG/JPG · paste or URL",
    };
  }
  if (kind === "audio") {
    return {
      title: "Drop audio track",
      hint: "MP3, WAV, or M4A · drag, browse, or drop",
    };
  }
  return {
    title: "Drop file here",
    hint: "Drag & drop, browse, or paste",
  };
}

function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function acceptMatches(file: File, accept?: string): boolean {
  if (!accept) return true;
  const tokens = accept.split(",").map((t) => t.trim().toLowerCase());
  return tokens.some((token) => {
    if (token.endsWith("/*")) {
      return file.type.startsWith(token.slice(0, -1));
    }
    if (token.startsWith(".")) {
      return file.name.toLowerCase().endsWith(token);
    }
    return file.type === token;
  });
}

function looksLikeImageUrl(raw: string): boolean {
  try {
    const u = new URL(raw.trim());
    if (u.protocol !== "http:" && u.protocol !== "https:") return false;
    return true;
  } catch {
    return false;
  }
}

function filenameFromUrl(url: string, mimeType: string): string {
  try {
    const path = new URL(url).pathname;
    const base = path.split("/").filter(Boolean).pop();
    if (base && /\.[a-z0-9]{2,5}$/i.test(base)) return decodeURIComponent(base);
  } catch {
    /* ignore */
  }
  const ext =
    mimeType === "image/png"
      ? "png"
      : mimeType === "image/webp"
        ? "webp"
        : mimeType === "image/gif"
          ? "gif"
          : "jpg";
  return `image-from-url.${ext}`;
}

export function FileUploadField({
  id,
  label,
  accept,
  helpText,
  value,
  onChange,
  hasError = false,
  errorMessage,
  disabled = false,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const inputId = useId();
  const urlInputId = useId();
  const kind = useMemo(() => detectKind(id, accept), [id, accept]);
  const copy = useMemo(() => kindCopy(kind, id), [kind, id]);
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<"accepted" | "rejecting" | null>(null);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [urlDraft, setUrlDraft] = useState("");
  const [showUrlField, setShowUrlField] = useState(false);
  const dragDepth = useRef(0);
  const feedbackTimer = useRef<number | null>(null);
  const progressTimer = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
      if (progressTimer.current) window.clearInterval(progressTimer.current);
    };
  }, []);

  const flashFeedback = useCallback((kind: "accepted" | "rejecting") => {
    setFeedback(kind);
    if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
    feedbackTimer.current = window.setTimeout(() => setFeedback(null), 420);
  }, []);

  const startProgress = useCallback(() => {
    setBusy(true);
    setProgress(8);
    if (progressTimer.current) window.clearInterval(progressTimer.current);
    progressTimer.current = window.setInterval(() => {
      setProgress((p) => {
        if (p >= 88) return p;
        return p + Math.max(2, Math.round((90 - p) * 0.12));
      });
    }, 90);
  }, []);

  const finishProgress = useCallback((ok: boolean) => {
    if (progressTimer.current) {
      window.clearInterval(progressTimer.current);
      progressTimer.current = null;
    }
    setProgress(ok ? 100 : 0);
    window.setTimeout(() => {
      setBusy(false);
      setProgress(0);
    }, ok ? 220 : 80);
  }, []);

  useEffect(() => {
    if (!value?.file || kind !== "image") {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(value.file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [value, kind]);

  const applyFile = useCallback(
    (file: File | null | undefined) => {
      if (!file) {
        onChange(null);
        setLocalError(null);
        finishProgress(false);
        return;
      }
      startProgress();
      window.setTimeout(() => {
        if (!acceptMatches(file, accept)) {
          setLocalError(
            kind === "audio"
              ? "Please upload an audio file (MP3, WAV, or M4A)."
              : kind === "image"
                ? "Please upload an image file (PNG, JPG, or WebP)."
                : "That file type is not supported here."
          );
          flashFeedback("rejecting");
          finishProgress(false);
          return;
        }
        if (file.size > 50 * 1024 * 1024) {
          setLocalError("File is too large (max 50 MB).");
          flashFeedback("rejecting");
          finishProgress(false);
          return;
        }
        setLocalError(null);
        onChange({
          file,
          name: file.name,
          mimeType: file.type,
          size: file.size,
        });
        flashFeedback("accepted");
        finishProgress(true);
      }, 160);
    },
    [accept, kind, onChange, flashFeedback, startProgress, finishProgress]
  );

  const applyImageFromUrl = useCallback(
    async (rawUrl: string) => {
      if (disabled || kind !== "image") return;
      const url = rawUrl.trim();
      if (!looksLikeImageUrl(url)) {
        setLocalError("Enter a valid http(s) image URL.");
        flashFeedback("rejecting");
        return;
      }
      startProgress();
      setLocalError(null);
      try {
        const res = await fetch(url, { mode: "cors", credentials: "omit" });
        if (!res.ok) {
          throw new Error(`Could not fetch image (${res.status}).`);
        }
        const blob = await res.blob();
        const mime = blob.type || "image/jpeg";
        if (!mime.startsWith("image/")) {
          throw new Error("URL did not return an image.");
        }
        const file = new File([blob], filenameFromUrl(url, mime), { type: mime });
        if (!acceptMatches(file, accept || "image/*")) {
          throw new Error("Please use a PNG, JPG, or WebP image URL.");
        }
        if (file.size > 50 * 1024 * 1024) {
          throw new Error("File is too large (max 50 MB).");
        }
        onChange({
          file,
          name: file.name,
          mimeType: file.type,
          size: file.size,
        });
        setUrlDraft("");
        setShowUrlField(false);
        flashFeedback("accepted");
        finishProgress(true);
      } catch (err) {
        const msg =
          err instanceof Error
            ? err.message
            : "Could not load that URL. Try downloading the image, then upload it.";
        setLocalError(
          /Failed to fetch|NetworkError|CORS/i.test(msg)
            ? "Could not load that URL (blocked by the host). Download the image, then upload it."
            : msg
        );
        flashFeedback("rejecting");
        finishProgress(false);
      }
    },
    [accept, disabled, finishProgress, flashFeedback, kind, onChange, startProgress]
  );

  const onDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;
    dragDepth.current += 1;
    setDragging(true);
  };

  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragDepth.current = Math.max(0, dragDepth.current - 1);
    if (dragDepth.current === 0) setDragging(false);
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragDepth.current = 0;
    setDragging(false);
    if (disabled) return;
    applyFile(e.dataTransfer.files?.[0]);
  };

  const takeClipboardImage = useCallback(
    (clipboardData: DataTransfer | null) => {
      if (disabled || kind !== "image" || !clipboardData) return false;
      const items = clipboardData.items;
      if (items) {
        for (const item of items) {
          if (item.type.startsWith("image/")) {
            const file = item.getAsFile();
            if (file) {
              applyFile(file);
              return true;
            }
          }
        }
      }
      const text = clipboardData.getData("text")?.trim();
      if (text && looksLikeImageUrl(text)) {
        void applyImageFromUrl(text);
        return true;
      }
      return false;
    },
    [applyFile, applyImageFromUrl, disabled, kind]
  );

  const onPaste = useCallback(
    (e: React.ClipboardEvent) => {
      if (takeClipboardImage(e.clipboardData)) {
        e.preventDefault();
      }
    },
    [takeClipboardImage]
  );

  useEffect(() => {
    if (disabled || kind !== "image") return;
    const onWindowPaste = (e: ClipboardEvent) => {
      const root = rootRef.current;
      if (!root) return;
      const active = document.activeElement;
      const focusedInside = Boolean(active && root.contains(active));
      if (!focusedInside) return;
      if (takeClipboardImage(e.clipboardData)) {
        e.preventDefault();
      }
    };
    window.addEventListener("paste", onWindowPaste);
    return () => window.removeEventListener("paste", onWindowPaste);
  }, [disabled, kind, takeClipboardImage]);

  const showError = hasError || Boolean(localError);
  const displayError = errorMessage || localError;

  return (
    <div
      ref={rootRef}
      className={[
        "file-upload",
        `file-upload--${id}`,
        `file-upload--kind-${kind}`,
        showError ? "file-upload--error" : "",
        value ? "file-upload--filled" : "",
        dragging ? "file-upload--dragging" : "",
        disabled ? "file-upload--disabled" : "",
        busy ? "file-upload--busy" : "",
        feedback === "accepted" ? "file-upload--accepted" : "",
        feedback === "rejecting" ? "file-upload--rejecting" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      onPaste={onPaste}
    >
      <div className="file-upload-label-row">
        <label htmlFor={inputId} className="file-upload-label">
          {label}
        </label>
        {kind === "image" ? (
          <span className="file-upload-kbd" title="Paste image or image URL from clipboard">
            Ctrl+V
          </span>
        ) : null}
      </div>

      <div
        className="file-upload-dropzone"
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
        aria-busy={busy}
        aria-label={`${label}. ${copy.hint}`}
        onClick={() => {
          if (!disabled && !busy && !value) inputRef.current?.click();
        }}
        onKeyDown={(e) => {
          if (disabled || busy) return;
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            if (!value) inputRef.current?.click();
          }
        }}
        onDragEnter={onDragEnter}
        onDragLeave={onDragLeave}
        onDragOver={onDragOver}
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          accept={accept}
          className="file-upload-input"
          disabled={disabled || busy}
          onChange={(e) => {
            applyFile(e.target.files?.[0]);
            e.target.value = "";
          }}
        />

        <div
          className="file-upload-progress"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={busy ? progress : 0}
          aria-hidden={!busy}
        >
          <div
            className="file-upload-progress__fill"
            style={
              busy && progress > 0
                ? { width: `${progress}%`, transform: "none", animation: "none" }
                : undefined
            }
          />
        </div>
        {busy ? (
          <span className="file-upload-progress-label" aria-live="polite">
            {progress < 100 ? `Uploading… ${progress}%` : "Ready"}
          </span>
        ) : null}

        {value ? (
          <div className="file-upload-preview">
            {previewUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={previewUrl}
                alt=""
                className="file-upload-thumb"
              />
            ) : (
              <span className={`file-upload-icon file-upload-icon--${kind}`} aria-hidden>
                {kind === "audio" ? "♪" : "▣"}
              </span>
            )}
            <div className="file-upload-meta">
              <span className="file-upload-name" title={value.name}>
                {value.name}
              </span>
              <span className="file-upload-size">{formatBytes(value.size)}</span>
            </div>
            <div className="file-upload-actions">
              <button
                type="button"
                className="file-upload-action"
                disabled={disabled || busy}
                onClick={(e) => {
                  e.stopPropagation();
                  inputRef.current?.click();
                }}
              >
                Replace
              </button>
              <button
                type="button"
                className="file-upload-clear"
                disabled={disabled || busy}
                onClick={(e) => {
                  e.stopPropagation();
                  applyFile(null);
                }}
                aria-label="Remove file"
              >
                ×
              </button>
            </div>
          </div>
        ) : (
          <div className="file-upload-empty">
            <span className={`file-upload-icon file-upload-icon--${kind}`} aria-hidden>
              {kind === "audio" ? "♪" : kind === "image" ? "⧉" : "＋"}
            </span>
            <span className="file-upload-title">{copy.title}</span>
            <span className="file-upload-hint">{copy.hint}</span>
            <span className="file-upload-browse">Browse files</span>
          </div>
        )}
      </div>

      {kind === "image" ? (
        <div className="file-upload-url">
          {showUrlField ? (
            <form
              className="file-upload-url__form"
              onSubmit={(e) => {
                e.preventDefault();
                void applyImageFromUrl(urlDraft);
              }}
            >
              <input
                id={urlInputId}
                type="url"
                className="file-upload-url__input"
                placeholder="https://… paste image URL"
                value={urlDraft}
                disabled={disabled || busy}
                onChange={(e) => setUrlDraft(e.target.value)}
                autoComplete="off"
                aria-label="Image URL"
              />
              <button
                type="submit"
                className="file-upload-url__submit"
                disabled={disabled || busy || !urlDraft.trim()}
              >
                Use URL
              </button>
              <button
                type="button"
                className="file-upload-url__cancel"
                disabled={disabled || busy}
                onClick={() => {
                  setShowUrlField(false);
                  setUrlDraft("");
                }}
              >
                Cancel
              </button>
            </form>
          ) : (
            <button
              type="button"
              className="file-upload-url__toggle"
              disabled={disabled || busy}
              onClick={() => setShowUrlField(true)}
            >
              Paste image URL
            </button>
          )}
        </div>
      ) : null}

      {showError && displayError ? (
        <p className="field-error" role="alert">
          {displayError}
        </p>
      ) : null}
      {helpText && !showError ? <p className="help">{helpText}</p> : null}
    </div>
  );
}

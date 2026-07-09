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
      hint: "Clear front-facing photo · PNG/JPG · or paste from clipboard",
    };
  }
  if (id === "productImage") {
    return {
      title: "Drop product image",
      hint: "Clean product shot on neutral background · PNG/JPG",
    };
  }
  if (id === "sourceImage") {
    return {
      title: "Drop source image",
      hint: "Image to animate · PNG/JPG/WebP",
    };
  }
  if (id === "coverImage") {
    return {
      title: "Drop cover art",
      hint: "Podcast / episode artwork · PNG/JPG",
    };
  }
  if (id === "referenceImage") {
    return {
      title: "Drop reference image",
      hint: "Style or scene reference · PNG/JPG",
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
  const inputId = useId();
  const kind = useMemo(() => detectKind(id, accept), [id, accept]);
  const copy = useMemo(() => kindCopy(kind, id), [kind, id]);
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<"accepted" | "rejecting" | null>(null);
  const [busy, setBusy] = useState(false);
  const dragDepth = useRef(0);
  const feedbackTimer = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
    };
  }, []);

  const flashFeedback = useCallback((kind: "accepted" | "rejecting") => {
    setFeedback(kind);
    if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
    feedbackTimer.current = window.setTimeout(() => setFeedback(null), 420);
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
        setBusy(false);
        return;
      }
      setBusy(true);
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
          setBusy(false);
          return;
        }
        if (file.size > 50 * 1024 * 1024) {
          setLocalError("File is too large (max 50 MB).");
          flashFeedback("rejecting");
          setBusy(false);
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
        setBusy(false);
      }, 160);
    },
    [accept, kind, onChange, flashFeedback]
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

  const onPaste = useCallback(
    (e: React.ClipboardEvent) => {
      if (disabled || kind !== "image") return;
      const items = e.clipboardData?.items;
      if (!items) return;
      for (const item of items) {
        if (item.type.startsWith("image/")) {
          const file = item.getAsFile();
          if (file) {
            e.preventDefault();
            applyFile(file);
            return;
          }
        }
      }
    },
    [applyFile, disabled, kind]
  );

  const showError = hasError || Boolean(localError);
  const displayError = errorMessage || localError;

  return (
    <div
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
          <span className="file-upload-kbd" title="Paste image from clipboard">
            ⌘V
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
          if (!disabled && !busy) inputRef.current?.click();
        }}
        onKeyDown={(e) => {
          if (disabled || busy) return;
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            inputRef.current?.click();
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

        <div className="file-upload-progress" aria-hidden>
          <div className="file-upload-progress__fill" />
        </div>
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
            <button
              type="button"
              className="file-upload-clear"
              disabled={disabled}
              onClick={(e) => {
                e.stopPropagation();
                applyFile(null);
              }}
              aria-label="Remove file"
            >
              ×
            </button>
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

      {showError && displayError ? (
        <p className="field-error" role="alert">
          {displayError}
        </p>
      ) : null}
      {helpText && !showError ? <p className="help">{helpText}</p> : null}
    </div>
  );
}

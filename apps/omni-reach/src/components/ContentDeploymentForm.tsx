"use client";

import { useCallback, useState, type DragEvent } from "react";
import { useOmniReachProfile } from "@/context/OmniReachProfileContext";
import type { FileFieldValue } from "@/lib/studio-form";

const PUBLISH_LOCK_MESSAGE = "Action locked. Review Tester Session metrics.";

type MediaDropZoneProps = {
  id: string;
  label: string;
  accept: string;
  hint: string;
  value: FileFieldValue | null;
  onChange: (value: FileFieldValue | null) => void;
  disabled?: boolean;
};

function fileFromList(file: File | undefined): FileFieldValue | null {
  if (!file) return null;
  return {
    file,
    name: file.name,
    mimeType: file.type,
    size: file.size,
  };
}

function MediaDropZone({
  id,
  label,
  accept,
  hint,
  value,
  onChange,
  disabled = false,
}: MediaDropZoneProps) {
  const [dragActive, setDragActive] = useState(false);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files?.length || disabled) return;
      onChange(fileFromList(files[0]));
    },
    [disabled, onChange]
  );

  const onDragOver = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    if (!disabled) setDragActive(true);
  };

  const onDragLeave = () => setDragActive(false);

  const onDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setDragActive(false);
    handleFiles(event.dataTransfer.files);
  };

  return (
    <div className="deployment-dropzone-wrap">
      <span className="deployment-field-label">{label}</span>
      <label
        htmlFor={id}
        className={`deployment-dropzone${dragActive ? " deployment-dropzone--active" : ""}${
          value ? " deployment-dropzone--filled" : ""
        }${disabled ? " deployment-dropzone--disabled" : ""}`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        <input
          id={id}
          type="file"
          accept={accept}
          className="deployment-dropzone__input"
          disabled={disabled}
          onChange={(event) => handleFiles(event.target.files)}
        />
        <div className="deployment-dropzone__inner">
          <span className="deployment-dropzone__icon" aria-hidden>
            ↑
          </span>
          <p className="deployment-dropzone__title">
            {value ? value.name : "Drag & drop or browse"}
          </p>
          <p className="deployment-dropzone__hint">{hint}</p>
        </div>
      </label>
      {value ? (
        <button
          type="button"
          className="deployment-dropzone__clear"
          disabled={disabled}
          onClick={() => onChange(null)}
        >
          Remove file
        </button>
      ) : null}
    </div>
  );
}

export function ContentDeploymentForm() {
  const { profile, testerLimitReached } = useOmniReachProfile();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [keywords, setKeywords] = useState("");
  const [videoFile, setVideoFile] = useState<FileFieldValue | null>(null);
  const [thumbnailFile, setThumbnailFile] = useState<FileFieldValue | null>(null);
  const [busy, setBusy] = useState(false);
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [scheduledAt, setScheduledAt] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const publishLocked = Boolean(testerLimitReached);

  const resetForm = () => {
    setTitle("");
    setDescription("");
    setKeywords("");
    setVideoFile(null);
    setThumbnailFile(null);
    setScheduledAt("");
    setScheduleOpen(false);
  };

  const submitDeployment = useCallback(
    async (mode: "publish" | "schedule") => {
      if (!profile?.id) {
        setError("Sign in to deploy content.");
        return;
      }
      if (publishLocked && mode === "publish") {
        setError(PUBLISH_LOCK_MESSAGE);
        return;
      }
      if (!title.trim()) {
        setError("Title is required.");
        return;
      }
      if (!videoFile) {
        setError("Select a video file before deploying.");
        return;
      }
      if (mode === "schedule" && !scheduledAt) {
        setError("Choose a schedule date and time.");
        return;
      }

      setBusy(true);
      setError(null);
      setNotice(null);

      try {
        const res = await fetch("/api/campaigns", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: title.trim(),
            description: description.trim() || null,
            keywords: keywords.trim() || null,
            videoFileName: videoFile.name,
            thumbnailFileName: thumbnailFile?.name ?? null,
            videoDurationSeconds: 30,
            mode,
            scheduledAt: mode === "schedule" ? scheduledAt : null,
          }),
        });
        const data = (await res.json().catch(() => ({}))) as {
          error?: string;
          message?: string;
        };
        if (!res.ok) {
          setError(data.error ?? "Deployment failed.");
          return;
        }
        setNotice(
          data.message ??
            (mode === "schedule"
              ? "Post scheduled across connected platforms."
              : "Queued for publishing to connected platforms.")
        );
        resetForm();
      } catch {
        setError("Deployment failed. Try again.");
      } finally {
        setBusy(false);
      }
    },
    [
      profile?.id,
      publishLocked,
      title,
      description,
      keywords,
      videoFile,
      thumbnailFile,
      scheduledAt,
    ]
  );

  return (
    <section className="content-deployment-panel" aria-label="Content deployment">
      <header className="content-deployment-panel__header">
        <p className="content-deployment-panel__eyebrow">Omni Reach Deployment</p>
        <h3>Unified Content Posting</h3>
        <p className="content-deployment-panel__intro">
          Prepare captions, media assets, and publish to every linked channel from one
          cinematic control surface.
        </p>
      </header>

      {error ? <p className="content-deployment-panel__error">{error}</p> : null}
      {notice ? <p className="content-deployment-panel__notice">{notice}</p> : null}

      <div className="content-deployment-form">
        <div className="deployment-field">
          <label htmlFor="deployment-title">Title</label>
          <input
            id="deployment-title"
            type="text"
            placeholder="Campaign headline for all connected platforms"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            disabled={busy}
          />
        </div>

        <div className="deployment-field">
          <label htmlFor="deployment-description">Description / Caption</label>
          <textarea
            id="deployment-description"
            placeholder="Write your cross-platform caption. Markdown supported for rich formatting."
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            disabled={busy}
            rows={5}
          />
          <p className="deployment-field__hint">Supports **bold**, _italic_, and line breaks.</p>
        </div>

        <div className="deployment-field">
          <label htmlFor="deployment-keywords">Keywords / Tags</label>
          <input
            id="deployment-keywords"
            type="text"
            placeholder="ai video, brand launch, omni reach"
            value={keywords}
            onChange={(event) => setKeywords(event.target.value)}
            disabled={busy}
          />
        </div>

        <div className="deployment-media-grid">
          <MediaDropZone
            id="deployment-video"
            label="Video Selection"
            accept="video/*"
            hint="MP4, MOV, or WebM up to your plan duration cap"
            value={videoFile}
            onChange={setVideoFile}
            disabled={busy}
          />
          <MediaDropZone
            id="deployment-thumbnail"
            label="Thumbnail Selection"
            accept="image/*"
            hint="PNG or JPG cover frame for feed previews"
            value={thumbnailFile}
            onChange={setThumbnailFile}
            disabled={busy}
          />
        </div>

        {scheduleOpen ? (
          <div className="deployment-schedule-panel">
            <label htmlFor="deployment-schedule-at">Schedule date & time</label>
            <input
              id="deployment-schedule-at"
              type="datetime-local"
              value={scheduledAt}
              onChange={(event) => setScheduledAt(event.target.value)}
              disabled={busy}
            />
          </div>
        ) : null}

        <div className="deployment-actions">
          <div className="deployment-actions__primary-wrap">
            <button
              type="button"
              className="deployment-actions__publish"
              disabled={busy || publishLocked}
              onClick={() => void submitDeployment("publish")}
            >
              {busy ? "Deploying..." : "Publish to Connected Platforms"}
            </button>
            {publishLocked ? (
              <div className="deployment-actions__lock-overlay" role="alert">
                <p>{PUBLISH_LOCK_MESSAGE}</p>
              </div>
            ) : null}
          </div>
          <button
            type="button"
            className="deployment-actions__schedule"
            disabled={busy}
            onClick={() => {
              if (scheduleOpen) {
                void submitDeployment("schedule");
              } else {
                setScheduleOpen(true);
                setError(null);
              }
            }}
          >
            {scheduleOpen ? "Confirm Schedule Post" : "Schedule Post"}
          </button>
          {scheduleOpen ? (
            <button
              type="button"
              className="deployment-actions__cancel-schedule"
              disabled={busy}
              onClick={() => {
                setScheduleOpen(false);
                setScheduledAt("");
              }}
            >
              Cancel schedule
            </button>
          ) : null}
        </div>
      </div>
    </section>
  );
}

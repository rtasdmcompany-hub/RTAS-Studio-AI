"use client";

import { Button } from "@rtas/ui";
import { truncatePreview } from "@/lib/studio-form-backup";
import type { StudioDraftSnapshot } from "@/lib/studio-form-backup";

type Props = {
  draft: StudioDraftSnapshot;
  onRestore: () => void;
  onDismiss: () => void;
};

export function DraftRestoreBanner({ draft, onRestore, onDismiss }: Props) {
  const title = draft.text.videoTitle?.trim();
  const preview = title || truncatePreview(draft.text.mainPrompt ?? draft.text.prompt ?? "", 56);
  const fieldCount = Object.values(draft.text).filter((v) => v.trim().length > 0).length;

  return (
    <div className="studio-draft-banner" role="status">
      <div className="studio-draft-banner__body">
        <p className="studio-draft-banner__title">Autosaved draft found</p>
        <p className="studio-draft-banner__meta">
          {preview ? `"${preview}" · ` : null}
          {fieldCount} field{fieldCount === 1 ? "" : "s"} · Saved{" "}
          {new Date(draft.savedAt).toLocaleString()}
        </p>
        <p className="studio-draft-banner__note">
          Text & settings restore instantly. Re-attach image/audio files if needed.
        </p>
      </div>
      <div className="studio-draft-banner__actions">
        <Button variant="lavender" size="sm" onClick={onRestore}>
          Restore draft
        </Button>
        <Button variant="ghost" size="sm" onClick={onDismiss}>
          Start fresh
        </Button>
      </div>
    </div>
  );
}

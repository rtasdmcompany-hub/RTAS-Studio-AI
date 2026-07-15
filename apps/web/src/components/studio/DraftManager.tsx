"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Button, Dialog, DialogActions, DialogBody } from "@rtas/ui";
import {
  deleteDraft,
  duplicateDraft,
  listStudioDrafts,
  renameDraft,
  saveNamedDraft,
  searchDrafts,
  truncatePreview,
  type StudioDraftListItem,
  type StudioDraftSnapshot,
} from "@/lib/studio-form-backup";

type Props = {
  open: boolean;
  onClose: () => void;
  onRestore: (snapshot: StudioDraftSnapshot) => void;
  disabled?: boolean;
};

function formatSavedAt(iso: string): string {
  try {
    return new Date(iso).toLocaleString([], {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function DraftManager({ open, onClose, onRestore, disabled = false }: Props) {
  const [query, setQuery] = useState("");
  const [drafts, setDrafts] = useState<StudioDraftListItem[]>([]);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");

  const refresh = useCallback(() => {
    setDrafts(query.trim() ? searchDrafts(query) : listStudioDrafts());
  }, [query]);

  useEffect(() => {
    if (!open) return;
    setQuery("");
    setRenamingId(null);
    setRenameValue("");
    setDrafts(listStudioDrafts());
  }, [open]);

  useEffect(() => {
    if (!open) return;
    refresh();
  }, [open, query, refresh]);

  const emptyLabel = useMemo(() => {
    if (query.trim()) return "No drafts match your search.";
    return "No saved drafts yet. Autosave keeps your current work here.";
  }, [query]);

  const handleRestore = (item: StudioDraftListItem) => {
    onRestore(item.snapshot);
    onClose();
  };

  const handleDuplicate = (id: string) => {
    duplicateDraft(id);
    refresh();
  };

  const handleDelete = (id: string) => {
    if (!window.confirm("Delete this draft? This cannot be undone.")) return;
    deleteDraft(id);
    refresh();
  };

  const startRename = (item: StudioDraftListItem) => {
    setRenamingId(item.id);
    setRenameValue(item.name);
  };

  const commitRename = () => {
    if (!renamingId) return;
    renameDraft(renamingId, renameValue);
    setRenamingId(null);
    setRenameValue("");
    refresh();
  };

  const handleSaveNamed = () => {
    const name = window.prompt("Name for this draft", "Untitled draft");
    if (name == null) return;
    const saved = saveNamedDraft(name);
    if (!saved) {
      window.alert("Nothing to save yet — start a project first.");
      return;
    }
    refresh();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      variant="modal"
      title="Drafts"
      description="Resume, rename, or manage drafts saved on this device."
      closeOnEscape
      closeOnOverlayClick
      contentClassName="studio-draft-manager"
    >
      <DialogBody className="studio-draft-manager__body">
        <div className="studio-draft-manager__toolbar">
          <input
            type="search"
            className="studio-draft-manager__search"
            placeholder="Search drafts…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search drafts"
            autoFocus
          />
          <Button
            variant="lavender"
            size="sm"
            onClick={handleSaveNamed}
            disabled={disabled}
          >
            Save as…
          </Button>
        </div>

        {drafts.length === 0 ? (
          <p className="studio-draft-manager__empty">{emptyLabel}</p>
        ) : (
          <ul className="studio-draft-manager__list" role="list">
            {drafts.map((item) => {
              const preview =
                item.snapshot.text.directionPrompt?.trim() ||
                item.snapshot.text.mainPrompt?.trim() ||
                item.snapshot.text.prompt?.trim() ||
                "";
              const isRenaming = renamingId === item.id;

              return (
                <li key={item.id} className="studio-draft-manager__item">
                  <div className="studio-draft-manager__item-main">
                    {isRenaming ? (
                      <input
                        className="studio-draft-manager__rename-input"
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") commitRename();
                          if (e.key === "Escape") {
                            setRenamingId(null);
                            setRenameValue("");
                          }
                        }}
                        aria-label="Draft name"
                        autoFocus
                      />
                    ) : (
                      <p className="studio-draft-manager__name">{item.name}</p>
                    )}
                    <p className="studio-draft-manager__meta">
                      {item.categoryLabel ? `${item.categoryLabel} · ` : null}
                      Saved {formatSavedAt(item.savedAt)}
                      {preview ? ` · ${truncatePreview(preview, 42)}` : null}
                    </p>
                  </div>
                  <div className="studio-draft-manager__actions">
                    {isRenaming ? (
                      <>
                        <Button variant="lavender" size="sm" onClick={commitRename}>
                          Save
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setRenamingId(null);
                            setRenameValue("");
                          }}
                        >
                          Cancel
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button
                          variant="lavender"
                          size="sm"
                          disabled={disabled}
                          onClick={() => handleRestore(item)}
                        >
                          Continue
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={disabled}
                          onClick={() => startRename(item)}
                        >
                          Rename
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={disabled}
                          onClick={() => handleDuplicate(item.id)}
                        >
                          Duplicate
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={disabled}
                          onClick={() => handleDelete(item.id)}
                        >
                          Delete
                        </Button>
                      </>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </DialogBody>
      <DialogActions>
        <Button variant="ghost" onClick={onClose}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
}

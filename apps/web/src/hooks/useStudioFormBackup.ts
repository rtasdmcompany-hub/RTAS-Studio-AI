"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { GenerationMode, VideoCategory, VisualStyle } from "@rtas/shared";
import {
  createInitialFormState,
  pruneFormToVisible,
  type StudioFormState,
} from "@/lib/studio-form";
import {
  clearStudioDraft,
  draftDiffersFrom,
  draftHasRestorableContent,
  isStudioDraftSaveSuppressed,
  loadStudioDraft,
  rememberFieldValue,
  saveStudioDraft,
  seedFieldHistoryFromText,
  type StudioDraftSnapshot,
} from "@/lib/studio-form-backup";

type UseStudioFormBackupArgs = {
  mode: GenerationMode | null;
  category: VideoCategory | null;
  visualStyle: VisualStyle | null;
  form: StudioFormState;
  setMode: (mode: GenerationMode | null) => void;
  setCategory: (category: VideoCategory | null) => void;
  setVisualStyle: (style: VisualStyle | null) => void;
  setForm: React.Dispatch<React.SetStateAction<StudioFormState>>;
  setWizardStep?: (step: number) => void;
};

function applyDraftToState(
  draft: StudioDraftSnapshot,
  args: Pick<
    UseStudioFormBackupArgs,
    "setMode" | "setCategory" | "setVisualStyle" | "setForm" | "setWizardStep"
  >
): void {
  seedFieldHistoryFromText(draft.text);
  args.setMode(draft.mode);
  args.setCategory(draft.category);
  args.setVisualStyle(draft.visualStyle);
  args.setForm((prev) => {
    const base = createInitialFormState();
    const mergedText = { ...base.text, ...draft.text };
    if (!draft.category || !draft.mode) {
      return { ...prev, text: mergedText };
    }
    return pruneFormToVisible(
      { ...prev, text: mergedText },
      draft.category,
      draft.mode,
      draft.visualStyle
    );
  });
  args.setWizardStep?.(1);
}

export function useStudioFormBackup({
  mode,
  category,
  visualStyle,
  form,
  setMode,
  setCategory,
  setVisualStyle,
  setForm,
  setWizardStep,
}: UseStudioFormBackupArgs) {
  const hydratedRef = useRef(false);
  const [pendingDraft, setPendingDraft] = useState<StudioDraftSnapshot | null>(null);
  const [lastSavedAt, setLastSavedAt] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const draft = loadStudioDraft();
    if (draft && draftHasRestorableContent(draft)) {
      setPendingDraft(draft);
    }
    hydratedRef.current = true;
  }, []);

  useEffect(() => {
    if (!hydratedRef.current || isStudioDraftSaveSuppressed()) return;
    if (!mode || !visualStyle) return;

    setSaving(true);
    const timer = window.setTimeout(() => {
      saveStudioDraft({
        mode,
        category,
        visualStyle,
        text: form.text,
      });
      setLastSavedAt(new Date().toISOString());
      setSaving(false);
    }, 450);

    return () => {
      window.clearTimeout(timer);
    };
  }, [mode, category, visualStyle, form.text]);

  const rememberTextField = useCallback((fieldId: string, value: string) => {
    rememberFieldValue(fieldId, value);
  }, []);

  const restoreDraft = useCallback(() => {
    if (!pendingDraft) return;
    applyDraftToState(pendingDraft, {
      setMode,
      setCategory,
      setVisualStyle,
      setForm,
      setWizardStep,
    });
    setPendingDraft(null);
    setLastSavedAt(pendingDraft.savedAt);
  }, [
    pendingDraft,
    setCategory,
    setForm,
    setMode,
    setVisualStyle,
    setWizardStep,
  ]);

  const applyDraftSnapshot = useCallback(
    (draft: StudioDraftSnapshot) => {
      applyDraftToState(draft, {
        setMode,
        setCategory,
        setVisualStyle,
        setForm,
        setWizardStep,
      });
      saveStudioDraft({
        mode: draft.mode,
        category: draft.category,
        visualStyle: draft.visualStyle,
        text: draft.text,
      });
      setPendingDraft(null);
      setLastSavedAt(draft.savedAt);
    },
    [setCategory, setForm, setMode, setVisualStyle, setWizardStep]
  );

  const dismissDraft = useCallback(() => {
    clearStudioDraft();
    setPendingDraft(null);
  }, []);

  const draftDiffers =
    pendingDraft && mode && visualStyle
      ? draftDiffersFrom(pendingDraft, mode, category, visualStyle, form.text)
      : false;

  return {
    rememberTextField,
    pendingDraft,
    restoreDraft,
    applyDraftSnapshot,
    dismissDraft,
    lastSavedAt,
    saving,
    showDraftBanner: Boolean(pendingDraft && draftDiffers),
  };
}

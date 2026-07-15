"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { GenerationMode, VideoCategory, VisualStyle } from "@rtas/shared";
import {
  createInitialFormState,
  pruneFormToVisible,
  type FileFieldValue,
  type StudioFormState,
} from "@/lib/studio-form";
import {
  clearAllDraftFiles,
  draftFileToFileField,
  loadAllDraftFiles,
  removeDraftFile,
  saveDraftFile,
} from "@/lib/studio-draft-files";
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

type SetupPhase = "mode" | "category" | "style" | "title";

type UseStudioFormBackupArgs = {
  mode: GenerationMode | null;
  category: VideoCategory | null;
  visualStyle: VisualStyle | null;
  form: StudioFormState;
  wizardStep: number;
  setupPhase: SetupPhase;
  setMode: (mode: GenerationMode | null) => void;
  setCategory: (category: VideoCategory | null) => void;
  setVisualStyle: (style: VisualStyle | null) => void;
  setForm: React.Dispatch<React.SetStateAction<StudioFormState>>;
  setWizardStep?: (step: number) => void;
  setSetupPhase?: (phase: SetupPhase) => void;
};

async function applyDraftToState(
  draft: StudioDraftSnapshot,
  args: Pick<
    UseStudioFormBackupArgs,
    | "setMode"
    | "setCategory"
    | "setVisualStyle"
    | "setForm"
    | "setWizardStep"
    | "setSetupPhase"
  >
): Promise<void> {
  seedFieldHistoryFromText(draft.text);
  args.setMode(draft.mode);
  args.setCategory(draft.category);
  args.setVisualStyle(draft.visualStyle);

  const fileRecords = await loadAllDraftFiles();
  const files: Record<string, FileFieldValue> = {};
  for (const record of fileRecords) {
    files[record.fieldId] = draftFileToFileField(record);
  }

  args.setForm((prev) => {
    const base = createInitialFormState();
    const mergedText = { ...base.text, ...draft.text };
    const merged = {
      ...prev,
      text: mergedText,
      files: { ...prev.files, ...files },
    };
    if (!draft.category || !draft.mode) {
      return merged;
    }
    return pruneFormToVisible(
      merged,
      draft.category,
      draft.mode,
      draft.visualStyle ?? "avatar"
    );
  });

  if (typeof draft.wizardStep === "number") {
    args.setWizardStep?.(draft.wizardStep);
  } else {
    args.setWizardStep?.(1);
  }
  if (draft.setupPhase) {
    args.setSetupPhase?.(draft.setupPhase);
  } else if (draft.visualStyle && draft.category) {
    args.setSetupPhase?.("title");
  }
}

export function useStudioFormBackup({
  mode,
  category,
  visualStyle,
  form,
  wizardStep,
  setupPhase,
  setMode,
  setCategory,
  setVisualStyle,
  setForm,
  setWizardStep,
  setSetupPhase,
}: UseStudioFormBackupArgs) {
  const hydratedRef = useRef(false);
  const autoRestoredRef = useRef(false);
  const [pendingDraft, setPendingDraft] = useState<StudioDraftSnapshot | null>(null);
  const [lastSavedAt, setLastSavedAt] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [draftRestored, setDraftRestored] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const draft = loadStudioDraft();
      if (draft && draftHasRestorableContent(draft) && !autoRestoredRef.current) {
        autoRestoredRef.current = true;
        await applyDraftToState(draft, {
          setMode,
          setCategory,
          setVisualStyle,
          setForm,
          setWizardStep,
          setSetupPhase,
        });
        if (!cancelled) {
          setLastSavedAt(draft.savedAt);
          setDraftRestored(true);
          setPendingDraft(null);
        }
      } else if (draft && draftHasRestorableContent(draft)) {
        if (!cancelled) setPendingDraft(draft);
      }
      hydratedRef.current = true;
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- hydrate once on mount
  }, []);

  useEffect(() => {
    if (!hydratedRef.current || isStudioDraftSaveSuppressed()) return;
    if (!mode) return;

    setSaving(true);
    const timer = window.setTimeout(() => {
      saveStudioDraft({
        mode,
        category,
        visualStyle,
        text: form.text,
        wizardStep,
        setupPhase,
      });
      setLastSavedAt(new Date().toISOString());
      setSaving(false);
    }, 450);

    return () => {
      window.clearTimeout(timer);
    };
  }, [mode, category, visualStyle, form.text, wizardStep, setupPhase]);

  // Persist uploaded files to IndexedDB whenever they change
  useEffect(() => {
    if (!hydratedRef.current || isStudioDraftSaveSuppressed()) return;
    const entries = Object.entries(form.files);
    void (async () => {
      for (const [fieldId, value] of entries) {
        if (value?.file) {
          await saveDraftFile(fieldId, value.file);
        } else {
          await removeDraftFile(fieldId);
        }
      }
    })();
  }, [form.files]);

  const rememberTextField = useCallback((fieldId: string, value: string) => {
    rememberFieldValue(fieldId, value);
  }, []);

  const restoreDraft = useCallback(() => {
    if (!pendingDraft) return;
    void applyDraftToState(pendingDraft, {
      setMode,
      setCategory,
      setVisualStyle,
      setForm,
      setWizardStep,
      setSetupPhase,
    }).then(() => {
      setPendingDraft(null);
      setLastSavedAt(pendingDraft.savedAt);
      setDraftRestored(true);
    });
  }, [
    pendingDraft,
    setCategory,
    setForm,
    setMode,
    setVisualStyle,
    setWizardStep,
    setSetupPhase,
  ]);

  const applyDraftSnapshot = useCallback(
    (draft: StudioDraftSnapshot) => {
      void applyDraftToState(draft, {
        setMode,
        setCategory,
        setVisualStyle,
        setForm,
        setWizardStep,
        setSetupPhase,
      }).then(() => {
        saveStudioDraft({
          mode: draft.mode,
          category: draft.category,
          visualStyle: draft.visualStyle,
          text: draft.text,
          wizardStep: draft.wizardStep,
          setupPhase: draft.setupPhase,
          selectedTemplateId: draft.selectedTemplateId,
        });
        setPendingDraft(null);
        setLastSavedAt(draft.savedAt);
        setDraftRestored(true);
      });
    },
    [setCategory, setForm, setMode, setVisualStyle, setWizardStep, setSetupPhase]
  );

  const dismissDraft = useCallback(() => {
    clearStudioDraft();
    void clearAllDraftFiles();
    setPendingDraft(null);
    setDraftRestored(false);
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
    draftRestored,
    clearDraftRestored: () => setDraftRestored(false),
    showDraftBanner: Boolean(pendingDraft && draftDiffers),
  };
}

"use client";

import { useCallback, useEffect, useRef } from "react";
import type { GenerationMode, VideoCategory, VisualStyle } from "@rtas/shared";
import {
  createInitialFormState,
  pruneFormToVisible,
  type StudioFormState,
} from "@/lib/studio-form";
import {
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
};

function applyDraftToState(
  draft: StudioDraftSnapshot,
  setForm: UseStudioFormBackupArgs["setForm"]
): void {
  seedFieldHistoryFromText(draft.text);
  setForm({
    ...createInitialFormState(),
    text: {
      ...createInitialFormState().text,
      ...(draft.text.videoTitle ? { videoTitle: draft.text.videoTitle } : {}),
    },
  });
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
}: UseStudioFormBackupArgs) {
  const hydratedRef = useRef(false);

  useEffect(() => {
    const draft = loadStudioDraft();
    if (draft) {
      applyDraftToState(draft, setForm);
    }
    hydratedRef.current = true;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!hydratedRef.current || isStudioDraftSaveSuppressed()) return;
    if (!mode || !visualStyle) return;
    saveStudioDraft({
      mode,
      category,
      visualStyle,
      text: form.text,
    });
  }, [mode, category, visualStyle, form.text]);

  const rememberTextField = useCallback((fieldId: string, value: string) => {
    rememberFieldValue(fieldId, value);
  }, []);

  return { rememberTextField };
}

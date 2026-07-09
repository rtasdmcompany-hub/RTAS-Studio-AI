"use client";

import { useEffect } from "react";

export type StudioShortcutHandlers = {
  onGenerate?: () => void;
  onCancel?: () => void;
  onRetry?: () => void;
  onToggleScreen?: () => void;
  onSaveDraft?: () => void;
  enabled?: boolean;
};

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  if (target.isContentEditable) return true;
  return Boolean(target.closest("[contenteditable='true']"));
}

/**
 * Premium Studio shortcuts (Cursor / Runway style):
 * - ⌘/Ctrl + Enter → Generate
 * - Esc → Cancel waiting / dismiss
 * - ⌘/Ctrl + Shift + R → Retry last failed generation
 * - ⌘/Ctrl + . → Toggle Create / Preview
 * - ⌘/Ctrl + S → Force draft save feedback
 */
export function useStudioKeyboardShortcuts({
  onGenerate,
  onCancel,
  onRetry,
  onToggleScreen,
  onSaveDraft,
  enabled = true,
}: StudioShortcutHandlers) {
  useEffect(() => {
    if (!enabled) return;

    const onKeyDown = (e: KeyboardEvent) => {
      const meta = e.metaKey || e.ctrlKey;
      const key = e.key.toLowerCase();

      if (meta && key === "enter") {
        e.preventDefault();
        onGenerate?.();
        return;
      }

      if (meta && e.shiftKey && key === "r") {
        e.preventDefault();
        onRetry?.();
        return;
      }

      if (meta && key === ".") {
        e.preventDefault();
        onToggleScreen?.();
        return;
      }

      if (meta && key === "s") {
        e.preventDefault();
        onSaveDraft?.();
        return;
      }

      if (e.key === "Escape") {
        if (isEditableTarget(e.target) && !(e.target instanceof HTMLTextAreaElement)) {
          return;
        }
        onCancel?.();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [enabled, onGenerate, onCancel, onRetry, onToggleScreen, onSaveDraft]);
}

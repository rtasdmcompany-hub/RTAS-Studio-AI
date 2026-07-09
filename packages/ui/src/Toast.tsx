"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { cn } from "./lib/cn";
import { Button } from "./Button";

export type ToastTone = "success" | "error" | "info" | "warning";

export type ToastState = {
  id: number;
  tone: ToastTone;
  title: string;
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
};

export type ToastProps = {
  toast: ToastState | null;
  onDismiss: () => void;
  autoHideMs?: number;
  /** Extra class on the root (e.g. studio-toast for legacy CSS hooks). */
  className?: string;
  children?: ReactNode;
};

/**
 * App-wide toast. Keeps `studio-toast` class aliases so existing CSS continues to apply.
 */
export function Toast({ toast, onDismiss, autoHideMs = 5200, className }: ToastProps) {
  const [rendered, setRendered] = useState<ToastState | null>(toast);
  const [leaving, setLeaving] = useState(false);
  const leaveTimer = useRef<number | null>(null);

  useEffect(() => {
    if (toast) {
      if (leaveTimer.current) window.clearTimeout(leaveTimer.current);
      setLeaving(false);
      setRendered(toast);
      return;
    }
    if (!rendered) return;
    setLeaving(true);
    leaveTimer.current = window.setTimeout(() => {
      setRendered(null);
      setLeaving(false);
      leaveTimer.current = null;
    }, 160);
    return () => {
      if (leaveTimer.current) window.clearTimeout(leaveTimer.current);
    };
    // Intentionally only react to toast prop changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [toast]);

  useEffect(() => {
    if (!toast) return;
    if (toast.tone === "error" && toast.onAction) return;
    const id = window.setTimeout(onDismiss, autoHideMs);
    return () => window.clearTimeout(id);
  }, [toast, onDismiss, autoHideMs]);

  if (!rendered) return null;

  return (
    <div
      className={cn(
        "rtas-ui-toast",
        "studio-toast",
        `rtas-ui-toast--${rendered.tone}`,
        `studio-toast--${rendered.tone}`,
        leaving && "rtas-ui-toast--leaving studio-toast--leaving",
        className,
      )}
      role={rendered.tone === "error" ? "alert" : "status"}
      aria-live="polite"
    >
      <div className="rtas-ui-toast__body studio-toast__body">
        <p className="rtas-ui-toast__title studio-toast__title">{rendered.title}</p>
        {rendered.message ? (
          <p className="rtas-ui-toast__message studio-toast__message">{rendered.message}</p>
        ) : null}
      </div>
      <div className="rtas-ui-toast__actions studio-toast__actions">
        {rendered.actionLabel && rendered.onAction && !leaving ? (
          <Button variant="lavender" size="sm" onClick={rendered.onAction}>
            {rendered.actionLabel}
          </Button>
        ) : null}
        <button
          type="button"
          className="rtas-ui-toast__close studio-toast__close rtas-ui-focus-ring rtas-ui-skip-focus"
          onClick={onDismiss}
          aria-label="Dismiss notification"
        >
          ×
        </button>
      </div>
    </div>
  );
}

"use client";

import {
  useCallback,
  useEffect,
  useId,
  useRef,
  type HTMLAttributes,
  type ReactNode,
} from "react";
import { cn } from "./lib/cn";

export type DialogVariant = "paywall" | "modal" | "auth" | "checkout";

const OVERLAY_CLASS: Record<DialogVariant, string> = {
  paywall: "paywall-overlay",
  modal: "modal-overlay",
  auth: "auth-modal-overlay",
  checkout: "rtas-checkout-overlay",
};

const CONTENT_CLASS: Record<DialogVariant, string> = {
  paywall: "paywall-modal",
  modal: "modal",
  auth: "auth-modal",
  checkout: "rtas-checkout-modal",
};

const TITLE_CLASS: Record<DialogVariant, string> = {
  paywall: "paywall-title",
  modal: "rtas-dialog-title",
  auth: "rtas-dialog-title",
  checkout: "rtas-checkout-modal__title",
};

const DESC_CLASS: Record<DialogVariant, string> = {
  paywall: "paywall-desc",
  modal: "rtas-dialog-desc",
  auth: "rtas-dialog-desc",
  checkout: "rtas-checkout-modal__message",
};

export type DialogProps = {
  open: boolean;
  onClose?: () => void;
  variant?: DialogVariant;
  title?: string;
  titleId?: string;
  description?: string;
  descriptionId?: string;
  closeOnEscape?: boolean;
  closeOnOverlayClick?: boolean;
  overlayClassName?: string;
  contentClassName?: string;
  children: ReactNode;
  /** Decorative glow element (paywall modals) */
  showGlow?: boolean;
};

export function Dialog({
  open,
  onClose,
  variant = "paywall",
  title,
  titleId,
  description,
  descriptionId,
  closeOnEscape = true,
  closeOnOverlayClick = false,
  overlayClassName,
  contentClassName,
  children,
  showGlow = variant === "paywall",
}: DialogProps) {
  const autoTitleId = useId();
  const autoDescId = useId();
  const resolvedTitleId = titleId ?? (title ? autoTitleId : undefined);
  const resolvedDescId = descriptionId ?? (description ? autoDescId : undefined);
  const contentRef = useRef<HTMLDivElement>(null);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!open || !closeOnEscape || event.key !== "Escape" || !onClose) return;
      event.preventDefault();
      onClose();
    },
    [closeOnEscape, onClose, open],
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    contentRef.current?.focus();
    return () => previous?.focus();
  }, [open]);

  if (!open) return null;

  return (
    <div
      className={cn(OVERLAY_CLASS[variant], overlayClassName)}
      role="presentation"
      onClick={
        closeOnOverlayClick && onClose
          ? (event) => {
              if (event.target === event.currentTarget) onClose();
            }
          : undefined
      }
    >
      <div
        ref={contentRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={resolvedTitleId}
        aria-describedby={resolvedDescId}
        tabIndex={-1}
        className={cn(CONTENT_CLASS[variant], contentClassName, "rtas-ui-focus-ring")}
      >
        {showGlow ? <div className="paywall-glow" aria-hidden /> : null}
        {title ? (
          <h2 id={resolvedTitleId} className={TITLE_CLASS[variant]}>
            {title}
          </h2>
        ) : null}
        {description ? (
          <p id={resolvedDescId} className={DESC_CLASS[variant]}>
            {description}
          </p>
        ) : null}
        {children}
      </div>
    </div>
  );
}

export type DialogSectionProps = HTMLAttributes<HTMLDivElement>;

export function DialogBody({ className, ...props }: DialogSectionProps) {
  return <div className={cn("rtas-dialog-desc", className)} {...props} />;
}

export function DialogActions({ className, ...props }: DialogSectionProps) {
  return <div className={cn("modal-actions", className)} {...props} />;
}

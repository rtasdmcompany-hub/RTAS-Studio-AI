import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "./lib/cn";

export type AlertVariant = "info" | "success" | "warning" | "error";

export type AlertProps = HTMLAttributes<HTMLDivElement> & {
  variant?: AlertVariant;
  title?: string;
  message: ReactNode;
  hint?: ReactNode;
  icon?: ReactNode;
  onDismiss?: () => void;
  dismissLabel?: string;
  /** Apply legacy backend-notice class for existing pages */
  legacyBackend?: boolean;
  /** Apply legacy field-error styling */
  legacyField?: boolean;
};

const DEFAULT_ICONS: Record<AlertVariant, string> = {
  info: "ℹ",
  success: "✓",
  warning: "⚠",
  error: "✕",
};

export function Alert({
  variant = "info",
  title,
  message,
  hint,
  icon,
  onDismiss,
  dismissLabel = "Dismiss",
  legacyBackend = false,
  legacyField = false,
  className,
  children,
  ...props
}: AlertProps) {
  if (legacyField) {
    return (
      <p className={cn("field-error", className)} role="alert" {...props}>
        {message}
      </p>
    );
  }

  if (legacyBackend) {
    return (
      <div className={cn("backend-notice", className)} role="alert" {...props}>
        <div className="backend-notice-icon" aria-hidden>
          {icon ?? DEFAULT_ICONS[variant === "error" ? "warning" : variant]}
        </div>
        <div className="backend-notice-body">
          {title ? <p className="backend-notice-title">{title}</p> : null}
          <p className="backend-notice-text">{message}</p>
          {hint ? <p className="backend-notice-hint">{hint}</p> : null}
        </div>
        {onDismiss ? (
          <button
            type="button"
            className="backend-notice-dismiss rtas-ui-focus-ring"
            onClick={onDismiss}
            aria-label={dismissLabel}
          >
            ×
          </button>
        ) : null}
      </div>
    );
  }

  return (
    <div
      {...props}
      role="alert"
      className={cn("rtas-ui-alert", `rtas-ui-alert--${variant}`, className)}
    >
      <span className="rtas-ui-alert__icon" aria-hidden>
        {icon ?? DEFAULT_ICONS[variant]}
      </span>
      <div className="rtas-ui-alert__body">
        {title ? <p className="rtas-ui-alert__title">{title}</p> : null}
        <div className="rtas-ui-alert__message">{message}</div>
        {hint ? <p className="rtas-ui-alert__hint">{hint}</p> : null}
        {children ? <div className="rtas-ui-alert__actions">{children}</div> : null}
      </div>
      {onDismiss ? (
        <button
          type="button"
          className="rtas-ui-alert__dismiss rtas-ui-focus-ring"
          onClick={onDismiss}
          aria-label={dismissLabel}
        >
          ×
        </button>
      ) : null}
    </div>
  );
}

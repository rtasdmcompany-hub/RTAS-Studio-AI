import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "./lib/cn";

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "ghost"
  | "lavender"
  | "lavender-lg"
  | "paywall"
  | "paywall-tester"
  | "paywall-standard"
  | "asset-primary"
  | "asset-ghost"
  | "asset-danger"
  | "ui-primary"
  | "ui-ghost";

export type ButtonSize = "sm" | "md" | "lg";

const LEGACY_VARIANT_CLASS: Record<ButtonVariant, string> = {
  primary: "btn-primary",
  secondary: "btn-secondary",
  ghost: "btn-ghost",
  lavender: "rtas-btn-lavender",
  "lavender-lg": "rtas-btn-lavender rtas-btn-lavender--lg",
  paywall: "paywall-subscribe-btn",
  "paywall-tester": "paywall-subscribe-btn paywall-subscribe-btn--tester",
  "paywall-standard": "paywall-subscribe-btn paywall-subscribe-btn--standard",
  "asset-primary": "asset-card__btn asset-card__btn--primary",
  "asset-ghost": "asset-card__btn asset-card__btn--ghost",
  "asset-danger": "asset-card__btn asset-card__btn--danger",
  "ui-primary": "rtas-ui-btn btn-primary",
  "ui-ghost": "rtas-ui-btn btn-ghost",
};

/** Size classes apply to every variant so sm/md/lg stay consistent app-wide. */
const SIZE_CLASS: Record<ButtonSize, string> = {
  sm: "rtas-ui-btn--sm",
  md: "rtas-ui-btn--md",
  lg: "rtas-ui-btn--lg",
};

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
  loading?: boolean;
  loadingLabel?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
};

export function Button({
  variant = "primary",
  size = "md",
  fullWidth = false,
  loading = false,
  loadingLabel = "Loading",
  leftIcon,
  rightIcon,
  className,
  disabled,
  children,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      {...props}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cn(
        "rtas-ui-btn",
        LEGACY_VARIANT_CLASS[variant],
        SIZE_CLASS[size],
        fullWidth && "rtas-ui-btn--full",
        "rtas-ui-focus-ring rtas-ui-skip-focus",
        className,
      )}
    >
      {loading ? (
        <>
          <span className="rtas-ui-spinner rtas-ui-spinner--sm" aria-hidden />
          <span>{loadingLabel}</span>
        </>
      ) : (
        <>
          {leftIcon}
          {children}
          {rightIcon}
        </>
      )}
    </button>
  );
}

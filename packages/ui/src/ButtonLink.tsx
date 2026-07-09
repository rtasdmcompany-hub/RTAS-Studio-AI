import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";
import { cn } from "./lib/cn";
import type { ButtonSize, ButtonVariant } from "./Button";

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

const SIZE_CLASS: Record<ButtonSize, string> = {
  sm: "rtas-ui-btn--sm",
  md: "rtas-ui-btn--md",
  lg: "rtas-ui-btn--lg",
};

function isNativeHref(href: ComponentProps<typeof Link>["href"]): boolean {
  if (typeof href !== "string") return false;
  return (
    href.startsWith("#") ||
    href.startsWith("http://") ||
    href.startsWith("https://") ||
    href.startsWith("mailto:")
  );
}

export type ButtonLinkProps = Omit<ComponentProps<typeof Link>, "className"> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  className?: string;
};

/**
 * Link styled as a Button — same variants/sizes as Button for one CTA language.
 */
export function ButtonLink({
  variant = "lavender",
  size = "md",
  fullWidth = false,
  leftIcon,
  rightIcon,
  className,
  children,
  href,
  ...props
}: ButtonLinkProps) {
  const classes = cn(
    "rtas-ui-btn",
    LEGACY_VARIANT_CLASS[variant],
    SIZE_CLASS[size],
    fullWidth && "rtas-ui-btn--full",
    "rtas-ui-focus-ring rtas-ui-skip-focus",
    className,
  );

  if (isNativeHref(href)) {
    const { replace, scroll, prefetch, locale, ...rest } = props;
    void replace;
    void scroll;
    void prefetch;
    void locale;
    return (
      <a href={href as string} className={classes} {...rest}>
        {leftIcon}
        {children}
        {rightIcon}
      </a>
    );
  }

  return (
    <Link href={href} className={classes} {...props}>
      {leftIcon}
      {children}
      {rightIcon}
    </Link>
  );
}

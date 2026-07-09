import type { ReactNode } from "react";
import { cn } from "./lib/cn";
import { Button, type ButtonProps } from "./Button";
import { ButtonLink } from "./ButtonLink";

export type EmptyStateProps = {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  /** When set with actionLabel, renders a ButtonLink instead of Button. */
  actionHref?: string;
  actionVariant?: ButtonProps["variant"];
  className?: string;
};

export function EmptyState({
  icon = "📭",
  title,
  description,
  action,
  actionLabel,
  onAction,
  actionHref,
  actionVariant = "lavender",
  className,
}: EmptyStateProps) {
  let defaultAction: ReactNode = null;
  if (!action && actionLabel) {
    if (actionHref) {
      defaultAction = (
        <ButtonLink href={actionHref} variant={actionVariant}>
          {actionLabel}
        </ButtonLink>
      );
    } else if (onAction) {
      defaultAction = (
        <Button variant={actionVariant} onClick={onAction}>
          {actionLabel}
        </Button>
      );
    }
  }

  return (
    <div className={cn("rtas-ui-empty", className)} role="status">
      {icon ? <div className="rtas-ui-empty__icon" aria-hidden>{icon}</div> : null}
      <h3 className="rtas-ui-empty__title">{title}</h3>
      {description ? <p className="rtas-ui-empty__description">{description}</p> : null}
      {action ?? defaultAction}
    </div>
  );
}

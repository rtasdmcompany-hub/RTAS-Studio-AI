import type { ElementType, HTMLAttributes, ReactNode } from "react";
import { cn } from "./lib/cn";

export type CardVariant = "default" | "glass" | "interactive";

export type CardProps = HTMLAttributes<HTMLElement> & {
  variant?: CardVariant;
  /** Also apply legacy profile-card styling */
  legacyProfile?: boolean;
  /** Semantic element — default div; use article for status cards. */
  as?: ElementType;
  children: ReactNode;
};

export function Card({
  variant = "default",
  legacyProfile = false,
  as: Comp = "div",
  className,
  children,
  ...props
}: CardProps) {
  return (
    <Comp
      {...props}
      className={cn(
        "rtas-ui-card",
        variant === "glass" && "rtas-ui-card--glass",
        variant === "interactive" && "rtas-ui-card--interactive",
        legacyProfile && "profile-card",
        className,
      )}
    >
      {children}
    </Comp>
  );
}

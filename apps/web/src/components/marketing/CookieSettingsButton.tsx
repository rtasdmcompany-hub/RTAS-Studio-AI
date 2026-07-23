"use client";

import { Button } from "@rtas/ui";
import { openCookiePreferences } from "@/lib/analytics";

type Props = {
  className?: string;
  label?: string;
};

/** Reopen cookie preference panel (Necessary / Analytics / Marketing). */
export function CookieSettingsButton({
  className,
  label = "Cookie settings",
}: Props) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      className={className}
      onClick={() => openCookiePreferences()}
    >
      {label}
    </Button>
  );
}

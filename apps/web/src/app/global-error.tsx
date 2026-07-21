"use client";

import { useEffect } from "react";
import { ButtonLink } from "@rtas/ui";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[global-error]", error);
  }, [error]);

  return (
    <html lang="en">
      <body className="rtas-fullpage-state">
        <div className="rtas-fullpage-state__card" role="alert">
          <span className="rtas-fullpage-state__code" aria-hidden>
            500
          </span>
          <h1 className="rtas-fullpage-state__title">Something went wrong</h1>
          <p className="rtas-fullpage-state__desc">
            We hit an unexpected error. Our team has been notified. Try again or
            return home while we recover.
          </p>
          <div className="rtas-fullpage-state__actions">
            <button type="button" className="rtas-ui-btn rtas-ui-btn--lavender" onClick={reset}>
              Try again
            </button>
            <ButtonLink href="/" variant="ghost">
              Back to home
            </ButtonLink>
          </div>
        </div>
      </body>
    </html>
  );
}

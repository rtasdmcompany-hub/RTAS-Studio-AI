"use client";

import { useEffect } from "react";
import { Button, ButtonLink } from "@rtas/ui";

type Props = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function RouteError({ error, reset }: Props) {
  useEffect(() => {
    console.error("Route error:", error);
  }, [error]);

  return (
    <div className="rtas-fullpage-state">
      <div className="rtas-fullpage-state__card" role="alert" aria-live="assertive">
        <span className="rtas-fullpage-state__icon" aria-hidden>
          ⚠️
        </span>
        <h1 className="rtas-fullpage-state__title">Something went wrong</h1>
        <p className="rtas-fullpage-state__desc">
          An unexpected error interrupted this page. Your account and saved work are
          safe. You can try again, or return to the studio.
        </p>
        {error.digest ? (
          <p className="rtas-ui-field-hint">Reference: {error.digest}</p>
        ) : null}
        <div className="rtas-fullpage-state__actions">
          <Button variant="lavender" onClick={reset}>
            Try again
          </Button>
          <ButtonLink href="/studio" variant="ghost">
            Back to Studio
          </ButtonLink>
        </div>
      </div>
    </div>
  );
}

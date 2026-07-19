"use client";

import { useEffect } from "react";
import { Button, ButtonLink } from "@rtas/ui";

type Props = {
  error: Error & { digest?: string };
  reset: () => void;
};

/**
 * Catches errors in the root layout. Must define its own html/body.
 */
export default function GlobalError({ error, reset }: Props) {
  useEffect(() => {
    console.error("Global error:", error);
  }, [error]);

  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          background: "#0b0b12",
          color: "#f4f0ff",
          fontFamily:
            "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
        }}
      >
        <div
          role="alert"
          aria-live="assertive"
          style={{
            maxWidth: 420,
            padding: "2rem",
            textAlign: "center",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: 12,
          }}
        >
          <h1 style={{ fontSize: "1.35rem", margin: "0 0 0.75rem" }}>
            Something went wrong
          </h1>
          <p style={{ opacity: 0.85, lineHeight: 1.5, margin: "0 0 1.25rem" }}>
            An unexpected error interrupted the application shell. Your account and
            saved work are safe.
          </p>
          {error.digest ? (
            <p style={{ opacity: 0.6, fontSize: "0.85rem" }}>
              Reference: {error.digest}
            </p>
          ) : null}
          <div
            style={{
              display: "flex",
              gap: "0.75rem",
              justifyContent: "center",
              flexWrap: "wrap",
              marginTop: "1rem",
            }}
          >
            <Button variant="lavender" onClick={reset}>
              Try again
            </Button>
            <ButtonLink href="/studio" variant="ghost">
              Back to Studio
            </ButtonLink>
          </div>
        </div>
      </body>
    </html>
  );
}

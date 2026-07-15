"use client";

import { useEffect, useState } from "react";
import { Button, ButtonLink } from "@rtas/ui";

const STORAGE_KEY = "rtas_onboarding_dismissed_v1";

type Props = {
  firstName?: string;
};

/**
 * First-visit welcome strip for the dashboard — dismissible, no redesign of layout.
 * Helps a new user understand Studio → credits → library within ~60 seconds.
 */
export function DashboardWelcome({ firstName }: Props) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      if (sessionStorage.getItem(STORAGE_KEY) === "1") return;
      const params = new URLSearchParams(window.location.search);
      if (params.get("welcome") === "1" || params.get("onboarding") === "1") {
        setVisible(true);
        return;
      }
      if (!localStorage.getItem(STORAGE_KEY)) {
        setVisible(true);
      }
    } catch {
      /* private mode */
    }
  }, []);

  function dismiss() {
    try {
      localStorage.setItem(STORAGE_KEY, "1");
      sessionStorage.setItem(STORAGE_KEY, "1");
    } catch {
      /* ignore */
    }
    setVisible(false);
  }

  if (!visible) return null;

  const name = firstName?.trim() || "there";

  return (
    <aside
      className="dashboard-welcome"
      aria-label="Welcome to RTAS Studio AI"
    >
      <div className="dashboard-welcome__copy">
        <p className="dashboard-welcome__eyebrow">
          Welcome{name !== "there" ? `, ${name}` : ""}
        </p>
        <h2 className="dashboard-welcome__title">Your workspace in four steps</h2>
        <ol className="dashboard-welcome__steps">
          <li>
            <strong>Open Studio</strong> — choose a category and describe your scene.
          </li>
          <li>
            <strong>Track credits</strong> — one credit equals one second of finished video.
          </li>
          <li>
            <strong>Review results here</strong> — library, queue status, and billing live on this dashboard.
          </li>
          <li>
            <strong>Get support anytime</strong> — Help Center is always available in the header.
          </li>
        </ol>
      </div>
      <div className="dashboard-welcome__actions">
        <ButtonLink href="/studio" variant="lavender">
          Open Studio
        </ButtonLink>
        <ButtonLink href="/how-to-use" variant="ghost">
          Quick start guide
        </ButtonLink>
        <Button type="button" variant="ghost" onClick={dismiss}>
          Dismiss
        </Button>
      </div>
    </aside>
  );
}

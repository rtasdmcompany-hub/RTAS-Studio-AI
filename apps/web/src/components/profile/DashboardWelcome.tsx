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
      // Soft show once per browser if never dismissed
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
        <p className="dashboard-welcome__eyebrow">Welcome{name !== "there" ? `, ${name}` : ""}</p>
        <h2 className="dashboard-welcome__title">You&apos;re ready in four steps</h2>
        <ol className="dashboard-welcome__steps">
          <li>
            <strong>Open Studio</strong> — pick a category and describe your scene.
          </li>
          <li>
            <strong>Watch credits</strong> — 1 credit = 1 second of finished video.
          </li>
          <li>
            <strong>Find results here</strong> — library, queue, and plan live on this dashboard.
          </li>
          <li>
            <strong>Need help?</strong> — Help Center is always in the header.
          </li>
        </ol>
      </div>
      <div className="dashboard-welcome__actions">
        <ButtonLink href="/studio" variant="lavender">
          Start in Studio
        </ButtonLink>
        <ButtonLink href="/how-to-use" variant="ghost">
          60-second guide
        </ButtonLink>
        <Button type="button" variant="ghost" onClick={dismiss}>
          Dismiss
        </Button>
      </div>
    </aside>
  );
}

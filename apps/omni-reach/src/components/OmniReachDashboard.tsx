"use client";

import { useCallback, useState } from "react";
import { ConnectChannels } from "@/components/ConnectChannels";
import { ContentDeploymentForm } from "@/components/ContentDeploymentForm";
import { useOmniReachProfile } from "@/context/OmniReachProfileContext";

export function OmniReachDashboard() {
  const { profile, testerSubscription, syncFromServer } = useOmniReachProfile();
  const [debugOpen, setDebugOpen] = useState(false);
  const [debugBusy, setDebugBusy] = useState(false);
  const [debugMessage, setDebugMessage] = useState<string | null>(null);

  const showDebugPanel =
    process.env.NODE_ENV === "development" &&
    profile?.tier === "tester" &&
    Boolean(testerSubscription);

  const handleResetTesterSession = useCallback(async () => {
    if (!profile?.id) return;
    setDebugBusy(true);
    setDebugMessage(null);
    try {
      const res = await fetch("/api/tester/debug/reset", { method: "POST" });
      const data = (await res.json().catch(() => ({}))) as {
        error?: string;
        ok?: boolean;
      };
      if (!res.ok || !data.ok) {
        setDebugMessage(data.error ?? "Could not reset tester session.");
        return;
      }
      await syncFromServer(profile.id);
      setDebugMessage("Tester session reset. Seconds refilled and expiry extended.");
    } catch {
      setDebugMessage("Could not reset tester session.");
    } finally {
      setDebugBusy(false);
    }
  }, [profile?.id, syncFromServer]);

  if (!profile) {
    return <p className="omni-loading">Loading Omni Reach…</p>;
  }

  return (
    <div className="omni-dashboard">
      <header className="omni-dashboard__hero">
        <p className="omni-dashboard__eyebrow">RTAS Omni Reach AI</p>
        <h1>Multi-Platform Publishing Studio</h1>
        <p>
          Connect channels, prepare ready-made media, and publish or schedule across
          every linked platform from one control surface.
        </p>
      </header>

      <ConnectChannels />
      <ContentDeploymentForm />

      {showDebugPanel && testerSubscription ? (
        <aside
          className={`tester-debug-panel${debugOpen ? " tester-debug-panel--open" : ""}`}
          aria-label="Omni Reach tester debug panel"
        >
          <button
            type="button"
            className="tester-debug-panel__toggle"
            onClick={() => setDebugOpen((open) => !open)}
          >
            {debugOpen ? "Hide Tester QA" : "Show Tester QA"}
          </button>
          {debugOpen ? (
            <div className="tester-debug-panel__body">
              <h3>Tester QA Panel</h3>
              <dl className="tester-debug-panel__grid">
                <div>
                  <dt>secondsUsed</dt>
                  <dd>{testerSubscription.secondsUsed}</dd>
                </div>
                <div>
                  <dt>remainingSeconds</dt>
                  <dd>{testerSubscription.remainingSeconds}</dd>
                </div>
                <div>
                  <dt>endDate</dt>
                  <dd>{new Date(testerSubscription.endDate).toLocaleString()}</dd>
                </div>
                <div>
                  <dt>isActive</dt>
                  <dd>{testerSubscription.isActive ? "true" : "false"}</dd>
                </div>
              </dl>
              <button
                type="button"
                className="tester-debug-panel__action"
                onClick={() => void handleResetTesterSession()}
                disabled={debugBusy}
              >
                {debugBusy ? "Resetting..." : "Reset Tester Session"}
              </button>
              {debugMessage ? (
                <p className="tester-debug-panel__message" role="status">
                  {debugMessage}
                </p>
              ) : null}
            </div>
          ) : null}
        </aside>
      ) : null}
    </div>
  );
}

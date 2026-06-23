"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { PlatformIcon } from "@/components/PlatformIcon";

export type SocialChannelStatus = {
  platform: "YOUTUBE" | "TIKTOK" | "INSTAGRAM" | "FACEBOOK" | "X" | "LINKEDIN";
  connected: boolean;
  expiresAt: string | null;
  updatedAt: string | null;
};

const TOKEN_WARNING_DAYS = 14;

function formatLastSynced(updatedAt: string | null): string | null {
  if (!updatedAt) return null;
  const diffMs = Date.now() - new Date(updatedAt).getTime();
  if (diffMs < 60_000) return "just now";
  const minutes = Math.floor(diffMs / 60_000);
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

function getTokenLifecycle(expiresAt: string | null): {
  state: "valid" | "warning" | "expired" | "none";
  label: string;
} {
  if (!expiresAt) {
    return { state: "none", label: "No token on file" };
  }

  const expiry = new Date(expiresAt);
  const diffMs = expiry.getTime() - Date.now();
  const daysLeft = Math.ceil(diffMs / (24 * 60 * 60 * 1000));

  if (daysLeft <= 0) {
    return { state: "expired", label: "Token Status: Expired — reconnect required" };
  }
  if (daysLeft <= TOKEN_WARNING_DAYS) {
    return {
      state: "warning",
      label: `Token Status: Refresh soon (expires in ${daysLeft}d)`,
    };
  }
  return {
    state: "valid",
    label: `Token Status: Valid (expires in ${daysLeft}d)`,
  };
}

const PLATFORM_META: Record<
  SocialChannelStatus["platform"],
  { label: string; accent: string; description: string }
> = {
  YOUTUBE: {
    label: "YouTube",
    accent: "#ff4d4f",
    description: "Long-form video, Shorts, and channel publishing.",
  },
  TIKTOK: {
    label: "TikTok",
    accent: "#25f4ee",
    description: "Short-form clips and viral launch distribution.",
  },
  INSTAGRAM: {
    label: "Instagram",
    accent: "#d62976",
    description: "Reels, feed publishing, and creator growth channels.",
  },
  FACEBOOK: {
    label: "Facebook",
    accent: "#1877f2",
    description: "Page publishing and audience retargeting content flows.",
  },
  X: {
    label: "X (Twitter)",
    accent: "#cbd5e1",
    description: "Realtime content drops and announcement distribution.",
  },
  LINKEDIN: {
    label: "LinkedIn",
    accent: "#0a66c2",
    description: "Business thought leadership and B2B campaign publishing.",
  },
};

function openPlaceholderPopup(platformLabel: string) {
  const popup = window.open("", "_blank", "width=560,height=720");
  if (!popup) return;
  popup.document.write(`
    <html>
      <head>
        <title>${platformLabel} OAuth Placeholder</title>
        <style>
          body { font-family: Segoe UI, sans-serif; background: #0a0b10; color: #f0f2f8; padding: 32px; }
          .card { border: 1px solid #2a2f45; border-radius: 16px; padding: 24px; background: #12141f; }
          h1 { margin-top: 0; }
          p { color: #cbd5e1; line-height: 1.6; }
        </style>
      </head>
      <body>
        <div class="card">
          <h1>${platformLabel} Connect</h1>
          <p>This is a placeholder OAuth redirection window for the RTAS Omni Reach AI channel registry.</p>
          <p>In production, this popup will redirect to the platform consent screen and return an access token to the secure token registry.</p>
          <p>You can close this window.</p>
        </div>
      </body>
    </html>
  `);
  popup.document.close();
}

export function ConnectChannels() {
  const [channels, setChannels] = useState<SocialChannelStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyPlatform, setBusyPlatform] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const loadChannels = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/social/connect", { cache: "no-store" });
      const data = (await res.json().catch(() => ({}))) as {
        error?: string;
        channels?: SocialChannelStatus[];
      };
      if (!res.ok) {
        setError(data.error ?? "Could not load connected channels.");
        setChannels([]);
        return;
      }
      setChannels(data.channels ?? []);
    } catch {
      setError("Could not load connected channels.");
      setChannels([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadChannels();
  }, [loadChannels]);

  const orderedChannels = useMemo(() => {
    return channels.length > 0
      ? channels
      : (Object.keys(PLATFORM_META) as SocialChannelStatus["platform"][]).map((platform) => ({
          platform,
          connected: false,
          expiresAt: null,
          updatedAt: null,
        }));
  }, [channels]);

  const connectPlatform = useCallback(async (platform: SocialChannelStatus["platform"]) => {
    setBusyPlatform(platform);
    setError(null);
    setNotice(null);
    openPlaceholderPopup(PLATFORM_META[platform].label);
    try {
      const demoExpiryDays =
        process.env.NODE_ENV === "development" && platform === "TIKTOK" ? 9 : 59;
      const res = await fetch("/api/social/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          platform,
          accessToken: `demo-token-${platform.toLowerCase()}-${Date.now()}`,
          refreshToken: `demo-refresh-${platform.toLowerCase()}`,
          expiresAt: new Date(
            Date.now() + demoExpiryDays * 24 * 60 * 60 * 1000
          ).toISOString(),
          allowReplace: false,
        }),
      });
      const data = (await res.json().catch(() => ({}))) as {
        error?: string;
        channels?: SocialChannelStatus[];
      };
      if (!res.ok) {
        setError(data.error ?? `Could not connect ${PLATFORM_META[platform].label}.`);
        return;
      }
      setChannels(data.channels ?? []);
      setNotice(`${PLATFORM_META[platform].label} connected in placeholder mode.`);
    } catch {
      setError(`Could not connect ${PLATFORM_META[platform].label}.`);
    } finally {
      setBusyPlatform(null);
    }
  }, []);

  const disconnectPlatform = useCallback(async (platform: SocialChannelStatus["platform"]) => {
    setBusyPlatform(platform);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch(
        `/api/social/connect?platform=${encodeURIComponent(platform)}`,
        { method: "DELETE" }
      );
      const data = (await res.json().catch(() => ({}))) as {
        error?: string;
        channels?: SocialChannelStatus[];
      };
      if (!res.ok) {
        setError(data.error ?? `Could not disconnect ${PLATFORM_META[platform].label}.`);
        return;
      }
      setChannels(data.channels ?? []);
      setNotice(`${PLATFORM_META[platform].label} disconnected.`);
    } catch {
      setError(`Could not disconnect ${PLATFORM_META[platform].label}.`);
    } finally {
      setBusyPlatform(null);
    }
  }, []);

  return (
    <section className="connect-channels-panel" aria-label="Connect channels">
      <div className="connect-channels-panel__header">
        <div>
          <p className="connect-channels-panel__eyebrow">Omni-Publishing Registry</p>
          <h3>Connect Channels</h3>
          <p className="connect-channels-panel__intro">
            Bind one active channel per platform so RTAS Omni Reach AI knows exactly where
            each campaign is eligible to publish.
          </p>
        </div>
        <button
          type="button"
          className="connect-channels-panel__refresh"
          onClick={() => void loadChannels()}
          disabled={loading}
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error ? <p className="connect-channels-panel__error">{error}</p> : null}
      {notice ? <p className="connect-channels-panel__notice">{notice}</p> : null}

      <div className="connect-channels-grid">
        {orderedChannels.map((channel) => {
          const meta = PLATFORM_META[channel.platform];
          const busy = busyPlatform === channel.platform;
          const lastSynced = channel.connected
            ? formatLastSynced(channel.updatedAt)
            : null;
          const tokenLifecycle = channel.connected
            ? getTokenLifecycle(channel.expiresAt)
            : { state: "none" as const, label: "" };
          return (
            <article key={channel.platform} className="connect-channel-card">
              <div className="connect-channel-card__top">
                <div className="connect-channel-card__brand">
                  <div className="connect-channel-card__icon-wrap">
                    <PlatformIcon platform={channel.platform} />
                  </div>
                  <div>
                    <h4>{meta.label}</h4>
                    <p>{meta.description}</p>
                  </div>
                </div>
                <span
                  className={
                    channel.connected
                      ? "connect-channel-card__badge connect-channel-card__badge--linked"
                      : "connect-channel-card__badge"
                  }
                >
                  {channel.connected ? "Linked" : "Not linked"}
                </span>
              </div>

              <div className="connect-channel-card__meta">
                {channel.connected && lastSynced ? (
                  <span className="connect-channel-card__sync">
                    Last synced: {lastSynced}
                  </span>
                ) : (
                  <span className="connect-channel-card__sync connect-channel-card__sync--idle">
                    Last synced: —
                  </span>
                )}
                {channel.connected ? (
                  <span
                    className={`connect-channel-card__token connect-channel-card__token--${tokenLifecycle.state}`}
                  >
                    {tokenLifecycle.label}
                  </span>
                ) : (
                  <span className="connect-channel-card__token connect-channel-card__token--none">
                    Token Status: Not connected
                  </span>
                )}
              </div>

              <div className="connect-channel-card__actions">
                {channel.connected ? (
                  <button
                    type="button"
                    className="connect-channel-card__disconnect"
                    onClick={() => void disconnectPlatform(channel.platform)}
                    disabled={busy}
                  >
                    {busy ? "Disconnecting..." : "Disconnect"}
                  </button>
                ) : (
                  <button
                    type="button"
                    className="connect-channel-card__connect"
                    onClick={() => void connectPlatform(channel.platform)}
                    disabled={busy}
                  >
                    {busy ? "Connecting..." : `Connect ${meta.label}`}
                  </button>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

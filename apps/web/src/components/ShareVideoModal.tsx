"use client";

import { useCallback, useEffect, useMemo, useState, type MouseEvent } from "react";
import type { GeneratedVideo } from "@rtas/shared";
import { filenameFromVideoUrl } from "@rtas/shared";
import { Alert, Button, Dialog } from "@rtas/ui";
import {
  buildEmailShareUrl,
  buildFacebookShareUrl,
  buildLinkedInShareUrl,
  buildPinterestShareUrl,
  buildPublicShareUrl,
  buildRedditShareUrl,
  buildTelegramShareUrl,
  buildTwitterShareUrl,
  buildWhatsAppShareUrl,
  copyTextToClipboard,
} from "@/lib/share-links";

type Props = {
  open: boolean;
  video: GeneratedVideo | null;
  onClose: () => void;
  onPublished?: (videoId: string) => void;
};

/** Channels that open a web intent vs copy-link for native apps */
const COPY_LINK_CHANNELS = new Set([
  "youtube",
  "instagram",
  "tiktok",
  "discord",
]);

const SOCIAL_CHANNELS = [
  { id: "youtube", label: "YouTube", className: "share-modal__social-btn--youtube" },
  { id: "instagram", label: "Instagram", className: "share-modal__social-btn--instagram" },
  { id: "tiktok", label: "TikTok", className: "share-modal__social-btn--tiktok" },
  { id: "facebook", label: "Facebook", className: "share-modal__social-btn--facebook" },
  { id: "linkedin", label: "LinkedIn", className: "share-modal__social-btn--linkedin" },
  { id: "pinterest", label: "Pinterest", className: "share-modal__social-btn--pinterest" },
  { id: "reddit", label: "Reddit", className: "share-modal__social-btn--reddit" },
  { id: "discord", label: "Discord", className: "share-modal__social-btn--discord" },
  { id: "telegram", label: "Telegram", className: "share-modal__social-btn--telegram" },
  { id: "whatsapp", label: "WhatsApp", className: "share-modal__social-btn--whatsapp" },
  { id: "x", label: "X", className: "share-modal__social-btn--x" },
  { id: "email", label: "Email", className: "share-modal__social-btn--email" },
] as const;

export function ShareVideoModal({ open, video, onClose, onPublished }: Props) {
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [copiedPrompt, setCopiedPrompt] = useState(false);
  const [actionNote, setActionNote] = useState<string | null>(null);

  const publicUrl = useMemo(
    () => (video ? buildPublicShareUrl(video.id) : ""),
    [video]
  );

  const publishShare = useCallback(async () => {
    if (!video?.videoUrl) return;

    setPublishing(true);
    setError(null);

    try {
      const res = await fetch(`/api/share/${encodeURIComponent(video.id)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: video.title,
          prompt: video.creativePrompt ?? null,
          videoUrl: video.videoUrl,
          durationSeconds: video.durationSeconds,
          category: video.category,
          visualStyle: video.visualStyle,
          mode: video.mode,
        }),
      });

      const data = (await res.json().catch(() => ({}))) as { error?: string };
      if (!res.ok) {
        throw new Error(data.error ?? "Unable to create share link.");
      }

      onPublished?.(video.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create share link.");
    } finally {
      setPublishing(false);
    }
  }, [video, onPublished]);

  useEffect(() => {
    if (!open || !video) return;
    setCopied(false);
    setCopiedPrompt(false);
    setActionNote(null);
    void publishShare();
  }, [open, video, publishShare]);

  const handleCopy = async () => {
    const ok = await copyTextToClipboard(publicUrl);
    setCopied(ok);
    if (ok) {
      window.setTimeout(() => setCopied(false), 2200);
    }
  };

  const handleCopyPrompt = async () => {
    const prompt = video?.creativePrompt?.trim();
    if (!prompt) {
      setActionNote("No creative prompt is available for this video yet.");
      return;
    }
    const ok = await copyTextToClipboard(prompt);
    setCopiedPrompt(ok);
    setActionNote(ok ? null : "Unable to copy prompt. Try again.");
    if (ok) {
      window.setTimeout(() => setCopiedPrompt(false), 2200);
    }
  };

  const handleDownloadVideo = () => {
    if (!video?.videoUrl || !video.canDownload) {
      setActionNote(
        video?.canDownload === false
          ? "Downloading requires an active commercial plan."
          : "This video is not ready to download yet."
      );
      return;
    }
    const a = document.createElement("a");
    a.href = video.videoUrl;
    a.download = filenameFromVideoUrl(video.videoUrl) || `${video.title || "rtas-video"}.mp4`;
    a.rel = "noopener";
    a.target = "_blank";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setActionNote("Download started.");
  };

  const handleDownloadImage = () => {
    const url = video?.thumbnailUrl;
    if (!url) {
      setActionNote(
        "No thumbnail is available for this render yet. Download the MP4 instead."
      );
      return;
    }
    const a = document.createElement("a");
    a.href = url;
    a.download = `${(video?.title || "rtas-thumb").replace(/[^\w\-]+/g, "-").slice(0, 48)}.jpg`;
    a.rel = "noopener";
    a.target = "_blank";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setActionNote("Thumbnail download started.");
  };

  if (!video) return null;

  const hrefFor = (id: (typeof SOCIAL_CHANNELS)[number]["id"]) => {
    switch (id) {
      case "x":
        return buildTwitterShareUrl(publicUrl, video.title);
      case "facebook":
        return buildFacebookShareUrl(publicUrl);
      case "linkedin":
        return buildLinkedInShareUrl(publicUrl);
      case "whatsapp":
        return buildWhatsAppShareUrl(publicUrl, video.title);
      case "telegram":
        return buildTelegramShareUrl(publicUrl, video.title);
      case "reddit":
        return buildRedditShareUrl(publicUrl, video.title);
      case "pinterest":
        return buildPinterestShareUrl(publicUrl, video.title);
      case "email":
        return buildEmailShareUrl(publicUrl, video.title);
      default:
        return publicUrl;
    }
  };

  const handleChannelClick = async (
    e: MouseEvent,
    id: (typeof SOCIAL_CHANNELS)[number]["id"]
  ) => {
    if (blocked) {
      e.preventDefault();
      return;
    }
    if (!COPY_LINK_CHANNELS.has(id)) return;
    e.preventDefault();
    const ok = await copyTextToClipboard(publicUrl);
    const label = SOCIAL_CHANNELS.find((c) => c.id === id)?.label ?? id;
    setActionNote(
      ok
        ? `Link copied. Open ${label} and paste to share.`
        : "Unable to copy link. Use Copy link instead."
    );
  };

  const description = publishing
    ? "Publishing your public link…"
    : error
      ? "We couldn’t publish this share link yet."
      : "Anyone with the link can watch. Share to social, copy the prompt, or download assets.";

  const blocked = publishing || Boolean(error);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      variant="paywall"
      titleId="share-modal-title"
      title="Share your video"
      description={description}
      closeOnEscape
      closeOnOverlayClick
      overlayClassName="share-modal-overlay"
      contentClassName="share-modal"
    >
      {error ? (
        <Alert variant="error" message={error} className="share-modal__error-alert" />
      ) : null}

      <div className="share-modal__link-bar">
        <input
          type="text"
          readOnly
          value={publicUrl}
          className="share-modal__link-input rtas-ui-input"
          aria-label="Public share link"
        />
        <Button
          variant="paywall"
          className="share-modal__copy-btn"
          onClick={() => void handleCopy()}
          disabled={blocked}
        >
          {copied ? "Copied" : "Copy link"}
        </Button>
      </div>

      <p className="share-modal__channels-label">Share to</p>
      <div className="share-modal__social" aria-label="Share to social channels">
        {SOCIAL_CHANNELS.map((channel) => (
          <a
            key={channel.id}
            href={hrefFor(channel.id)}
            target={channel.id === "email" || COPY_LINK_CHANNELS.has(channel.id) ? undefined : "_blank"}
            rel={
              channel.id === "email" || COPY_LINK_CHANNELS.has(channel.id)
                ? undefined
                : "noopener noreferrer"
            }
            className={`share-modal__social-btn ${channel.className}`}
            aria-disabled={blocked}
            onClick={(e) => {
              void handleChannelClick(e, channel.id);
            }}
          >
            {channel.label}
          </a>
        ))}
      </div>

      <p className="share-modal__channels-label">Assets & prompt</p>
      <div className="share-modal__actions" aria-label="Download assets and copy prompt">
        <Button
          variant="secondary"
          size="sm"
          onClick={handleDownloadVideo}
          disabled={!video.videoUrl}
        >
          Download MP4
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleDownloadImage}
          disabled={!video.thumbnailUrl}
          title={
            video.thumbnailUrl
              ? "Download thumbnail image"
              : "No thumbnail is available for this render yet"
          }
        >
          Download thumbnail
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => void handleCopyPrompt()}
          disabled={!video.creativePrompt?.trim()}
        >
          {copiedPrompt ? "Prompt copied" : "Copy prompt"}
        </Button>
        <a
          href={publicUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="share-modal__social-btn share-modal__social-btn--public"
        >
          Open public page
        </a>
      </div>

      {actionNote ? (
        <p className="share-modal__action-note" role="status">
          {actionNote}
        </p>
      ) : null}

      <button type="button" className="paywall-skip-link rtas-ui-focus-ring" onClick={onClose}>
        Close
      </button>
    </Dialog>
  );
}

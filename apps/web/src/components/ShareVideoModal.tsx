"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { GeneratedVideo } from "@rtas/shared";
import { filenameFromVideoUrl } from "@rtas/shared";
import { Alert, Button, Dialog } from "@rtas/ui";
import {
  buildEmailShareUrl,
  buildFacebookShareUrl,
  buildLinkedInShareUrl,
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

const SOCIAL_CHANNELS = [
  { id: "x", label: "X", className: "share-modal__social-btn--x" },
  { id: "facebook", label: "Facebook", className: "share-modal__social-btn--facebook" },
  { id: "linkedin", label: "LinkedIn", className: "share-modal__social-btn--linkedin" },
  { id: "whatsapp", label: "WhatsApp", className: "share-modal__social-btn--whatsapp" },
  { id: "telegram", label: "Telegram", className: "share-modal__social-btn--telegram" },
  { id: "reddit", label: "Reddit", className: "share-modal__social-btn--reddit" },
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
      setActionNote("No prompt saved for this render yet.");
      return;
    }
    const ok = await copyTextToClipboard(prompt);
    setCopiedPrompt(ok);
    setActionNote(ok ? null : "Could not copy prompt.");
    if (ok) {
      window.setTimeout(() => setCopiedPrompt(false), 2200);
    }
  };

  const handleDownloadVideo = () => {
    if (!video?.videoUrl || !video.canDownload) {
      setActionNote(
        video?.canDownload === false
          ? "Download requires an active commercial subscription."
          : "Video file is not ready to download yet."
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
  };

  const handleDownloadImage = () => {
    setActionNote(
      "Poster image download will be available when thumbnail export ships. Use Download Video for now."
    );
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
      case "email":
        return buildEmailShareUrl(publicUrl, video.title);
      default:
        return publicUrl;
    }
  };

  const description = publishing
    ? "Publishing your public link…"
    : error
      ? "We could not publish this link yet."
      : "Your video is live for anyone with the link. Share, download, or copy the prompt.";

  const blocked = publishing || Boolean(error);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      variant="paywall"
      titleId="share-modal-title"
      title="Share your AI video"
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
          {copied ? "Copied!" : "Copy Link"}
        </Button>
      </div>

      <p className="share-modal__channels-label">Share to</p>
      <div className="share-modal__social" aria-label="Share to social">
        {SOCIAL_CHANNELS.map((channel) => (
          <a
            key={channel.id}
            href={hrefFor(channel.id)}
            target={channel.id === "email" ? undefined : "_blank"}
            rel={channel.id === "email" ? undefined : "noopener noreferrer"}
            className={`share-modal__social-btn ${channel.className}`}
            aria-disabled={blocked}
            onClick={(e) => {
              if (blocked) e.preventDefault();
            }}
          >
            {channel.label}
          </a>
        ))}
      </div>

      <p className="share-modal__channels-label">Project actions</p>
      <div className="share-modal__actions" aria-label="Project actions">
        <Button
          variant="secondary"
          size="sm"
          onClick={handleDownloadVideo}
          disabled={!video.videoUrl}
        >
          Download Video
        </Button>
        <Button variant="ghost" size="sm" onClick={handleDownloadImage}>
          Download Image
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => void handleCopyPrompt()}
          disabled={!video.creativePrompt?.trim()}
        >
          {copiedPrompt ? "Prompt copied!" : "Copy Prompt"}
        </Button>
        <a
          href={publicUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="share-modal__social-btn share-modal__social-btn--public"
        >
          Public page
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

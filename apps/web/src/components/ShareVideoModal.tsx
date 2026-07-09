"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { GeneratedVideo } from "@rtas/shared";
import { Alert, Button, Dialog } from "@rtas/ui";
import {
  buildPublicShareUrl,
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

export function ShareVideoModal({ open, video, onClose, onPublished }: Props) {
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

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
    void publishShare();
  }, [open, video, publishShare]);

  const handleCopy = async () => {
    const ok = await copyTextToClipboard(publicUrl);
    setCopied(ok);
    if (ok) {
      window.setTimeout(() => setCopied(false), 2200);
    }
  };

  if (!video) return null;

  const whatsAppUrl = buildWhatsAppShareUrl(publicUrl, video.title);
  const twitterUrl = buildTwitterShareUrl(publicUrl, video.title);
  const description = publishing
    ? "Publishing your public link…"
    : error
      ? "We could not publish this link yet."
      : "Your video is live for anyone with the link. Spread it across social channels.";

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
          disabled={publishing || Boolean(error)}
        >
          {copied ? "Copied!" : "Copy Public Link"}
        </Button>
      </div>

      <div className="share-modal__social" aria-label="Share to social">
        <a
          href={whatsAppUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="share-modal__social-btn share-modal__social-btn--whatsapp"
        >
          WhatsApp
        </a>
        <a
          href={twitterUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="share-modal__social-btn share-modal__social-btn--x"
        >
          X / Twitter
        </a>
        <button
          type="button"
          className="share-modal__social-btn share-modal__social-btn--copy rtas-ui-focus-ring"
          onClick={() => void handleCopy()}
          disabled={publishing || Boolean(error)}
        >
          Copy link
        </button>
      </div>

      <button type="button" className="paywall-skip-link rtas-ui-focus-ring" onClick={onClose}>
        Close
      </button>
    </Dialog>
  );
}

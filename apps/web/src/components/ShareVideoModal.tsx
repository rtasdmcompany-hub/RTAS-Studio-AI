"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { GeneratedVideo } from "@rtas/shared";
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

  if (!open || !video) return null;

  const whatsAppUrl = buildWhatsAppShareUrl(publicUrl, video.title);
  const twitterUrl = buildTwitterShareUrl(publicUrl, video.title);

  return (
    <div
      className="paywall-overlay share-modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="share-modal-title"
      onClick={onClose}
    >
      <div
        className="paywall-modal share-modal"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="paywall-glow" aria-hidden />
        <h2 id="share-modal-title" className="paywall-title">
          Share your AI video
        </h2>
        <p className="paywall-desc">
          {publishing
            ? "Publishing your public link…"
            : error
              ? "We could not publish this link yet."
              : "Your video is live for anyone with the link. Spread it across social channels."}
        </p>

        {error ? (
          <p className="share-modal__error" role="alert">
            {error}
          </p>
        ) : null}

        <div className="share-modal__link-bar">
          <input
            type="text"
            readOnly
            value={publicUrl}
            className="share-modal__link-input"
            aria-label="Public share link"
          />
          <button
            type="button"
            className="share-modal__copy-btn"
            onClick={() => void handleCopy()}
            disabled={publishing || Boolean(error)}
          >
            {copied ? "Copied!" : "Copy Public Link"}
          </button>
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
            className="share-modal__social-btn share-modal__social-btn--copy"
            onClick={() => void handleCopy()}
            disabled={publishing || Boolean(error)}
          >
            Copy link
          </button>
        </div>

        <button type="button" className="paywall-skip-link" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}

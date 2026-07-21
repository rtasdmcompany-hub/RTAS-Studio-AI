"use client";

import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { VideoPlayer } from "@/components/VideoPlayer";
import { resolveVideoPlaybackUrl } from "@/lib/video-playback";
import type { PublicSharePayload } from "@/lib/share-types";

type Props = {
  share: PublicSharePayload;
};

export function SharePublicView({ share }: Props) {
  const playbackSrc = resolveVideoPlaybackUrl(share.videoUrl);

  return (
    <div className="share-page">
      <header className="share-page__header">
        <Link href="/" className="share-page__brand">
          {PRODUCT_NAME}
        </Link>
        <span className="share-page__badge">Public showcase</span>
      </header>

      <main className="share-page__main">
        <section className="share-page__hero">
          <p className="share-page__eyebrow">AI-generated with RTAS Studio</p>
          <h1 className="share-page__title">{share.title}</h1>
          <p className="share-page__meta">
            {share.durationSeconds}s · {share.category} · {share.visualStyle} style
          </p>
        </section>

        <div className="share-page__player-wrap">
          <VideoPlayer src={playbackSrc} title={share.title} />
        </div>

        {share.prompt ? (
          <section className="share-page__prompt" aria-label="Creative prompt">
            <h2>Original creative prompt</h2>
            <blockquote>{share.prompt}</blockquote>
          </section>
        ) : null}

        <section className="share-page__cta">
          <h2>Create your own AI video with {PRODUCT_NAME}</h2>
          <p>
            Turn prompts and images into cinematic videos — Identity Preservation, music sync, and
            studio-grade exports in minutes.
          </p>
          <Link href="/studio" className="share-page__cta-btn rtas-ui-focus-ring">
            Start creating <span aria-hidden>→</span>
          </Link>
        </section>
      </main>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef } from "react";

function ShowcaseVideo({ src }: { src: string }) {
  const ref = useRef<HTMLVideoElement>(null);

  const play = useCallback(() => {
    const video = ref.current;
    if (!video) return;
    void video.play().catch(() => {
      /* muted autoplay retry on next interaction */
    });
  }, []);

  useEffect(() => {
    play();
  }, [src, play]);

  return (
    <video
      ref={ref}
      src={src}
      autoPlay
      muted
      loop
      playsInline
      preload="auto"
      className="w-full h-full object-cover"
      onLoadedData={play}
      onCanPlay={play}
    />
  );
}

export function LandingCategoryShowcase({
  variant = "default",
}: {
  variant?: "default" | "hero";
}) {
  const rootClass =
    variant === "hero"
      ? "rtas-category-showcase rtas-category-showcase--hero"
      : "rtas-category-showcase";

  return (
    <div className={rootClass}>
      <Link href="/studio" className="rtas-category-card" aria-label="Rap — open studio">
        <span className="rtas-category-card__media">
          <ShowcaseVideo src="/showcase/rap.mp4" />
          <span className="rtas-category-card__sheen" aria-hidden />
        </span>
        <span className="rtas-category-card__body">
          <span className="rtas-category-card__label">Rap</span>
          <span className="rtas-category-card__blurb">Lyric-synced urban music videos</span>
        </span>
      </Link>

      <Link href="/studio" className="rtas-category-card" aria-label="Solo — open studio">
        <span className="rtas-category-card__media">
          <ShowcaseVideo src="/showcase/solo.mp4" />
          <span className="rtas-category-card__sheen" aria-hidden />
        </span>
        <span className="rtas-category-card__body">
          <span className="rtas-category-card__label">Solo</span>
          <span className="rtas-category-card__blurb">Solo performance &amp; narrative clips</span>
        </span>
      </Link>

      <Link href="/studio" className="rtas-category-card" aria-label="Commercial — open studio">
        <span className="rtas-category-card__media">
          <ShowcaseVideo src="/showcase/commercial.mp4" />
          <span className="rtas-category-card__sheen" aria-hidden />
        </span>
        <span className="rtas-category-card__body">
          <span className="rtas-category-card__label">Commercial</span>
          <span className="rtas-category-card__blurb">Product ads &amp; brand promos</span>
        </span>
      </Link>

      <Link href="/studio" className="rtas-category-card" aria-label="Cartoon — open studio">
        <span className="rtas-category-card__media">
          <ShowcaseVideo src="/showcase/cartoon.mp4" />
          <span className="rtas-category-card__sheen" aria-hidden />
        </span>
        <span className="rtas-category-card__body">
          <span className="rtas-category-card__label">Cartoon</span>
          <span className="rtas-category-card__blurb">Animated stories for kids</span>
        </span>
      </Link>

      <Link href="/studio" className="rtas-category-card" aria-label="Islamic — open studio">
        <span className="rtas-category-card__media">
          <ShowcaseVideo src="/showcase/islamic.mp4" />
          <span className="rtas-category-card__sheen" aria-hidden />
        </span>
        <span className="rtas-category-card__body">
          <span className="rtas-category-card__label">Islamic</span>
          <span className="rtas-category-card__blurb">Nasheeds, reminders &amp; Quran visuals</span>
        </span>
      </Link>
    </div>
  );
}

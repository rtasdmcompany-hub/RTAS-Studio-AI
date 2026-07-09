"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

function ShowcaseVideo({ src }: { src: string }) {
  const ref = useRef<HTMLVideoElement>(null);
  const [shouldLoad, setShouldLoad] = useState(false);

  const play = useCallback(() => {
    const video = ref.current;
    if (!video) return;
    void video.play().catch(() => {
      /* muted autoplay retry on next interaction */
    });
  }, []);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    if (typeof IntersectionObserver === "undefined") {
      setShouldLoad(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setShouldLoad(true);
          observer.disconnect();
        }
      },
      { rootMargin: "120px", threshold: 0.05 }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (shouldLoad) play();
  }, [src, shouldLoad, play]);

  return (
    <video
      ref={ref}
      src={shouldLoad ? src : undefined}
      autoPlay={shouldLoad}
      muted
      loop
      playsInline
      preload="none"
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
          <span className="rtas-category-card__blurb">Stylized animated storytelling</span>
        </span>
      </Link>

      <Link href="/studio" className="rtas-category-card" aria-label="Islamic — open studio">
        <span className="rtas-category-card__media">
          <ShowcaseVideo src="/showcase/islamic.mp4" />
          <span className="rtas-category-card__sheen" aria-hidden />
        </span>
        <span className="rtas-category-card__body">
          <span className="rtas-category-card__label">Islamic</span>
          <span className="rtas-category-card__blurb">Faith-forward cinematic storytelling</span>
        </span>
      </Link>
    </div>
  );
}

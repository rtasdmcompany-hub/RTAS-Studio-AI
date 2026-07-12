"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { ShowcaseItem } from "@/lib/ai-showcase";

function LazyShowcaseVideo({
  src,
  className,
  priority = false,
}: {
  src: string;
  className?: string;
  priority?: boolean;
}) {
  const ref = useRef<HTMLVideoElement>(null);
  const [shouldLoad, setShouldLoad] = useState(priority);

  const play = useCallback(() => {
    const video = ref.current;
    if (!video) return;
    void video.play().catch(() => {
      /* muted autoplay may require gesture on some browsers */
    });
  }, []);

  useEffect(() => {
    if (priority) return;
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
      { rootMargin: "160px", threshold: 0.05 }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [priority]);

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
      preload={priority ? "metadata" : "none"}
      className={className}
      onLoadedData={play}
      onCanPlay={play}
    />
  );
}

export function AiShowcaseHero({ item }: { item: ShowcaseItem }) {
  return (
    <div className="rtas-ai-showcase-hero-media" aria-label={`${item.title} preview`}>
      <LazyShowcaseVideo
        src={item.src}
        priority
        className="rtas-ai-showcase-hero-media__video"
      />
      <div className="rtas-ai-showcase-hero-media__veil" aria-hidden />
    </div>
  );
}

export function AiShowcaseGrid({ items }: { items: ShowcaseItem[] }) {
  return (
    <ul className="rtas-ai-showcase-grid">
      {items.map((item) => (
        <li key={item.id} className="rtas-ai-showcase-card">
          <div className="rtas-ai-showcase-card__media">
            <LazyShowcaseVideo src={item.src} className="rtas-ai-showcase-card__video" />
          </div>
          <div className="rtas-ai-showcase-card__body">
            <p className="rtas-ai-showcase-card__audience">{item.audience}</p>
            <h3>{item.title}</h3>
            <p>{item.blurb}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}

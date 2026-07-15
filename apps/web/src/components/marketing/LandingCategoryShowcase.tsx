"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

type ShowcaseCard = {
  id: string;
  label: string;
  blurb: string;
  video: string;
  poster: string;
};

const SHOWCASE_CARDS: ShowcaseCard[] = [
  {
    id: "rap",
    label: "Rap",
    blurb: "Lyric-synced urban music videos",
    video: "/showcase/rap.mp4",
    poster: "/categories/category-song.jpg",
  },
  {
    id: "solo",
    label: "Solo",
    blurb: "Solo performance & narrative clips",
    video: "/showcase/solo.mp4",
    poster: "/styles/style-real-face.jpg",
  },
  {
    id: "commercial",
    label: "Commercial",
    blurb: "Product ads & brand promos",
    video: "/showcase/commercial.mp4",
    poster: "/categories/category-business.jpg",
  },
  {
    id: "cartoon",
    label: "Cartoon",
    blurb: "Stylized animated storytelling",
    video: "/showcase/cartoon.mp4",
    poster: "/categories/category-cartoon.jpg",
  },
  {
    id: "islamic",
    label: "Islamic",
    blurb: "Faith-forward cinematic storytelling",
    video: "/showcase/islamic.mp4",
    poster: "/categories/category-religious.jpg",
  },
];

function ShowcaseVideo({ src, poster }: { src: string; poster: string }) {
  const ref = useRef<HTMLVideoElement>(null);
  const [shouldLoad, setShouldLoad] = useState(false);
  const [failed, setFailed] = useState(false);

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
    if (shouldLoad && !failed) play();
  }, [src, shouldLoad, failed, play]);

  if (failed) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={poster}
        alt=""
        className="w-full h-full object-cover"
        width={480}
        height={720}
        loading="lazy"
        decoding="async"
      />
    );
  }

  return (
    <video
      ref={ref}
      src={shouldLoad ? src : undefined}
      poster={poster}
      autoPlay={shouldLoad}
      muted
      loop
      playsInline
      preload="none"
      className="w-full h-full object-cover"
      onLoadedData={play}
      onCanPlay={play}
      onError={() => setFailed(true)}
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
      {SHOWCASE_CARDS.map((card) => (
        <Link
          key={card.id}
          href="/studio"
          className="rtas-category-card"
          aria-label={`${card.label} — open studio`}
        >
          <span className="rtas-category-card__media">
            <ShowcaseVideo src={card.video} poster={card.poster} />
            <span className="rtas-category-card__sheen" aria-hidden />
          </span>
          <span className="rtas-category-card__body">
            <span className="rtas-category-card__label">{card.label}</span>
            <span className="rtas-category-card__blurb">{card.blurb}</span>
          </span>
        </Link>
      ))}
    </div>
  );
}

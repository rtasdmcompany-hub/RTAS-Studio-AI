"use client";

import { useCallback, useEffect, useRef } from "react";

const PILLAR_VIDEOS = [
  { id: "p1", className: "rtas-pillar--a", src: "/showcase/rap.mp4" },
  { id: "p2", className: "rtas-pillar--b", src: "/showcase/solo.mp4" },
  { id: "p3", className: "rtas-pillar--c", src: "/showcase/commercial.mp4" },
  { id: "p4", className: "rtas-pillar--d", src: "/showcase/cartoon.mp4" },
  { id: "p5", className: "rtas-pillar--e", src: "/showcase/islamic.mp4" },
] as const;

function PillarVideo({ src }: { src: string }) {
  const videoRef = useRef<HTMLVideoElement>(null);

  const tryPlay = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    void video.play().catch(() => {
      /* autoplay policy — muted inline usually succeeds on retry */
    });
  }, []);

  useEffect(() => {
    tryPlay();
  }, [src, tryPlay]);

  return (
    <video
      ref={videoRef}
      className="rtas-pillar__video w-full h-full object-cover"
      src={src}
      autoPlay
      muted
      loop
      playsInline
      preload="auto"
      onLoadedData={tryPlay}
      onCanPlay={tryPlay}
    />
  );
}

/** Kaiber-style pillar backdrop — five staggered showcase loops behind the hero copy. */
export function HeroKaiberBackground() {
  return (
    <>
      <div className="rtas-kaiber-hero__ambient" aria-hidden>
        <PillarVideo src="/showcase/rap.mp4" />
      </div>
      <div className="rtas-kaiber-hero__pillars" aria-hidden>
        {PILLAR_VIDEOS.map((pillar) => (
          <div key={pillar.id} className={`rtas-pillar ${pillar.className}`}>
            <PillarVideo src={pillar.src} />
          </div>
        ))}
      </div>
      <div className="rtas-kaiber-hero__cyber-fx" aria-hidden />
      <div className="rtas-kaiber-hero__overlay" aria-hidden />
    </>
  );
}

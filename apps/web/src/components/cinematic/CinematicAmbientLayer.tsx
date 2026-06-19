"use client";

import { useCallback, useEffect, useRef } from "react";
import { LOCAL_SHOWCASE_CATEGORY_VIDEOS } from "@/lib/preview-showcase";
import { getStudioAmbientVideoIndex } from "@/lib/studio-ambient-scenes";

type Props = {
  /** Wizard group id, "setup", "preview", etc. — each gets a different backdrop clip. */
  scene?: string;
};

/** Full-screen cinematic backdrop — same local loops as the landing page. */
export function CinematicAmbientLayer({ scene = "default" }: Props) {
  const sourceIndex = getStudioAmbientVideoIndex(scene);
  const src =
    LOCAL_SHOWCASE_CATEGORY_VIDEOS[
      sourceIndex % LOCAL_SHOWCASE_CATEGORY_VIDEOS.length
    ];

  const videoRef = useRef<HTMLVideoElement>(null);

  const tryPlay = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    void video.play().catch(() => {});
  }, []);

  useEffect(() => {
    tryPlay();
  }, [src, tryPlay]);

  return (
    <div className="shashka-ambient" aria-hidden>
      <video
        ref={videoRef}
        key={src}
        className="shashka-ambient__video w-full h-full object-cover"
        src={src}
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
        onLoadedData={tryPlay}
        onCanPlay={tryPlay}
      />
      <div className="shashka-ambient__grade" />
      <div className="shashka-ambient__neon" />
      <div className="shashka-ambient__vignette" />
      <div className="shashka-ambient__grain" />
    </div>
  );
}

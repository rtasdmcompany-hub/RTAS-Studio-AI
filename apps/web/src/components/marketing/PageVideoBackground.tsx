"use client";

import { useCallback, useEffect, useRef } from "react";

type Props = {
  src: string;
  className?: string;
};

/** Full-screen page backdrop — 100% visible showcase loop (no dim overlay). */
export function PageVideoBackground({ src, className = "" }: Props) {
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
    <div className={`page-video-bg ${className}`.trim()} aria-hidden>
      <video
        ref={videoRef}
        key={src}
        className="page-video-bg__video"
        src={src}
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
        onLoadedData={tryPlay}
        onCanPlay={tryPlay}
      />
    </div>
  );
}

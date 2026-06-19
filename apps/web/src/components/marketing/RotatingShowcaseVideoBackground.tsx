"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { LOCAL_SHOWCASE_CATEGORY_VIDEOS } from "@/lib/preview-showcase";

const ROTATE_MS = 14_000;

/** Full-screen backdrop — cycles all 5 showcase loops at 100% visibility. */
export function RotatingShowcaseVideoBackground() {
  const [activeIndex, setActiveIndex] = useState(0);
  const videoRefs = useRef<(HTMLVideoElement | null)[]>([]);

  const tryPlay = useCallback((video: HTMLVideoElement | null) => {
    if (!video) return;
    void video.play().catch(() => {});
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActiveIndex((index) => (index + 1) % LOCAL_SHOWCASE_CATEGORY_VIDEOS.length);
    }, ROTATE_MS);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    LOCAL_SHOWCASE_CATEGORY_VIDEOS.forEach((_, index) => {
      if (index === activeIndex) tryPlay(videoRefs.current[index]);
    });
  }, [activeIndex, tryPlay]);

  return (
    <div className="page-video-bg rtas-global-showcase-video" aria-hidden>
      {LOCAL_SHOWCASE_CATEGORY_VIDEOS.map((src, index) => (
        <video
          key={src}
          ref={(element) => {
            videoRefs.current[index] = element;
          }}
          className={`page-video-bg__video${
            index === activeIndex ? " page-video-bg__video--active" : ""
          }`}
          src={src}
          autoPlay
          muted
          loop
          playsInline
          preload={index <= 1 ? "auto" : "metadata"}
          onLoadedData={(event) => tryPlay(event.currentTarget)}
          onCanPlay={(event) => tryPlay(event.currentTarget)}
        />
      ))}
    </div>
  );
}

"use client";

import { useCallback, useRef, useState } from "react";
import { LOCAL_SHOWCASE_CATEGORY_VIDEOS } from "@/lib/preview-showcase";

const RESULT_URLS = [...LOCAL_SHOWCASE_CATEGORY_VIDEOS];

/** 5s cinematic result — video with CSS fallback if stream fails. */
export function ShowcaseOutputDemo() {
  const [urlIndex, setUrlIndex] = useState(0);
  const [useFallback, setUseFallback] = useState(false);
  const tried = useRef(0);

  const src = RESULT_URLS[urlIndex] ?? RESULT_URLS[0];

  const onError = useCallback(() => {
    tried.current += 1;
    if (urlIndex < RESULT_URLS.length - 1) {
      setUrlIndex((i) => i + 1);
      return;
    }
    setUseFallback(true);
  }, [urlIndex]);

  return (
    <div className="showcase-output-demo" aria-label="Cinematic result preview">
      <div className="showcase-output-demo__header">
        <span className="showcase-output-demo__phase">Step 5 · Aapki final video</span>
        <span className="showcase-output-demo__badge">8K Cinematic</span>
      </div>
      {!useFallback ? (
        <video
          key={src}
          className="showcase-output-demo__video"
          src={src}
          autoPlay
          muted
          playsInline
          loop
          preload="auto"
          onError={onError}
        />
      ) : (
        <div className="showcase-output-demo__fallback" aria-hidden>
          <div className="showcase-output-demo__fallback-glow" />
          <div className="showcase-output-demo__fallback-scene" />
          <p className="showcase-output-demo__fallback-text">Cinematic render complete</p>
        </div>
      )}
      <div className="showcase-output-demo__caption">
        Generate ke baad yahi quality yahan play hogi — premium color, depth &amp; motion
      </div>
    </div>
  );
}

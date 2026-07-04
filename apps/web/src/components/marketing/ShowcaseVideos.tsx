"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

/**
 * Landing-only cinematic backdrop.
 *
 * The heavy showcase <video> elements are code-split (ssr: false) and mounted
 * only after the landing page has painted, so they never block first paint or
 * ship on non-home routes.
 */
const RotatingShowcaseVideoBackground = dynamic(
  () =>
    import("./RotatingShowcaseVideoBackground").then(
      (mod) => mod.RotatingShowcaseVideoBackground
    ),
  { ssr: false }
);

export function ShowcaseVideos() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const idleWindow = window as Window & {
      requestIdleCallback?: (cb: () => void) => number;
      cancelIdleCallback?: (handle: number) => void;
    };

    let idleHandle: number | undefined;
    let timeoutHandle: number | undefined;

    if (typeof idleWindow.requestIdleCallback === "function") {
      idleHandle = idleWindow.requestIdleCallback(() => setReady(true));
    } else {
      timeoutHandle = window.setTimeout(() => setReady(true), 200);
    }

    return () => {
      if (idleHandle !== undefined && idleWindow.cancelIdleCallback) {
        idleWindow.cancelIdleCallback(idleHandle);
      }
      if (timeoutHandle !== undefined) {
        window.clearTimeout(timeoutHandle);
      }
    };
  }, []);

  if (!ready) return null;
  return <RotatingShowcaseVideoBackground />;
}

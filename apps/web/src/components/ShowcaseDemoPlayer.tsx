"use client";

import {
  SHOWCASE_BADGE_SUBTITLE,
  SHOWCASE_BADGE_TITLE,
} from "@/lib/preview-showcase";

/** Default preview — moody cyber-rap urban showcase (no nature stock). */
export function ShowcaseDemoPlayer() {
  return (
    <div className="video-player-block">
      <div className="player-wrap player-wrap--showcase player-wrap--cyber-rap">
        <video
          className="player-video w-full h-full object-cover"
          src="/showcase/rap.mp4"
          playsInline
          autoPlay
          muted
          loop
          preload="auto"
        />
        <div className="cyber-rap-rain" aria-hidden />
        <div className="cyber-rap-neon" aria-hidden />
        <div className="cyber-rap-vignette" aria-hidden />
        <div className="showcase-quality-badge" aria-hidden>
          <span className="showcase-quality-badge__title">{SHOWCASE_BADGE_TITLE}</span>
          <span className="showcase-quality-badge__subtitle">{SHOWCASE_BADGE_SUBTITLE}</span>
        </div>
      </div>
    </div>
  );
}

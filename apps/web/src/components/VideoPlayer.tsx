"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { GenerationProgressOverlay } from "./GenerationProgressOverlay";
import { ShowcaseDemoPlayer } from "./ShowcaseDemoPlayer";
import {
  getVideoFallbackChain,
  getNextFallback,
  isShowcasePlayback,
  DEFAULT_SHOWCASE_URL,
  resolveVideoPlaybackUrl,
} from "@/lib/video-playback";

type Props = {
  src?: string;
  title?: string;
  isGenerating?: boolean;
  /** When false, progress is shown only via PreviewGenerationProgress above the player. */
  showProgressOverlay?: boolean;
  generationPercent?: number;
  generationMessage?: string;
  generationStageIndex?: number;
  generationPatienceMessage?: string;
};

export function VideoPlayer({
  src,
  title,
  isGenerating = false,
  showProgressOverlay = true,
  generationPercent = 0,
  generationMessage = "",
  generationStageIndex = 0,
  generationPatienceMessage = "",
}: Props) {
  const resolvedSrc = useMemo(
    () => resolveVideoPlaybackUrl(src) || DEFAULT_SHOWCASE_URL,
    [src]
  );
  const isShowcase = useMemo(
    () => isShowcasePlayback(src, resolvedSrc),
    [src, resolvedSrc]
  );
  const fallbackChain = useMemo(
    () => getVideoFallbackChain(resolvedSrc),
    [resolvedSrc]
  );
  const [playbackSrc, setPlaybackSrc] = useState(
    () => resolvedSrc || DEFAULT_SHOWCASE_URL
  );

  useEffect(() => {
    setPlaybackSrc(resolvedSrc || DEFAULT_SHOWCASE_URL);
  }, [resolvedSrc]);

  const handleVideoError = useCallback(() => {
    setPlaybackSrc((current) => {
      const next = getNextFallback(current, fallbackChain);
      return next ?? DEFAULT_SHOWCASE_URL;
    });
  }, [fallbackChain]);

  const hasSrc = Boolean(playbackSrc?.trim());
  const showEmpty = !hasSrc && !isGenerating;
  const showDownload = hasSrc && !isGenerating && !isShowcase;

  if (isShowcase && !isGenerating) {
    return <ShowcaseDemoPlayer />;
  }

  return (
    <div className="video-player-block">
      {title && !isGenerating && (
        <p className="video-player-title">{title}</p>
      )}
      <div className={`player-wrap ${isGenerating ? "player-wrap--busy" : ""}`}>
        {showEmpty && (
          <div className="player-empty rtas-ui-empty player-empty--inline" role="status">
            <span className="rtas-ui-empty__icon" aria-hidden>
              🎬
            </span>
            <p className="rtas-ui-empty__description">Generated video will appear here</p>
          </div>
        )}
        {hasSrc && !isGenerating && (
          <video
            key={playbackSrc}
            src={playbackSrc}
            controls
            playsInline
            preload="metadata"
            className="player-video"
            onError={handleVideoError}
          />
        )}
        {isGenerating && (
          <div className="player-generating-bg" aria-hidden />
        )}
        {showProgressOverlay ? (
          <GenerationProgressOverlay
            visible={isGenerating}
            percent={generationPercent}
            message={generationMessage}
            stageIndex={generationStageIndex}
            patienceMessage={generationPatienceMessage}
          />
        ) : null}
      </div>
      {showDownload ? (
        <div className="download-row">
          <a href={playbackSrc} download className="btn-download">
            Download video
          </a>
        </div>
      ) : null}
    </div>
  );
}

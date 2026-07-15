"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react";
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

const PLAYBACK_RATES = [0.5, 0.75, 1, 1.25, 1.5, 2] as const;
const FRAME_STEP = 1 / 30;

function formatPlayerTime(sec: number): string {
  if (!Number.isFinite(sec) || sec < 0) return "0:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

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

  const videoRef = useRef<HTMLVideoElement>(null);
  const playerRootRef = useRef<HTMLDivElement>(null);

  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [muted, setMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [loop, setLoop] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

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
  const showCustomControls = hasSrc && !isGenerating;

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !showCustomControls) return;

    const onPlay = () => setPlaying(true);
    const onPause = () => setPlaying(false);
    const onTime = () => setCurrentTime(video.currentTime || 0);
    const onMeta = () => setDuration(video.duration || 0);
    const onVol = () => {
      setVolume(video.volume);
      setMuted(video.muted);
    };
    const onRate = () => setPlaybackRate(video.playbackRate);
    const onLoop = () => setLoop(video.loop);

    video.addEventListener("play", onPlay);
    video.addEventListener("pause", onPause);
    video.addEventListener("timeupdate", onTime);
    video.addEventListener("loadedmetadata", onMeta);
    video.addEventListener("durationchange", onMeta);
    video.addEventListener("volumechange", onVol);
    video.addEventListener("ratechange", onRate);
    video.addEventListener("seeking", onTime);

    setPlaying(!video.paused);
    setCurrentTime(video.currentTime || 0);
    setDuration(video.duration || 0);
    setVolume(video.volume);
    setMuted(video.muted);
    setPlaybackRate(video.playbackRate);
    setLoop(video.loop);
    video.addEventListener("loadstart", onLoop);

    return () => {
      video.removeEventListener("play", onPlay);
      video.removeEventListener("pause", onPause);
      video.removeEventListener("timeupdate", onTime);
      video.removeEventListener("loadedmetadata", onMeta);
      video.removeEventListener("durationchange", onMeta);
      video.removeEventListener("volumechange", onVol);
      video.removeEventListener("ratechange", onRate);
      video.removeEventListener("seeking", onTime);
      video.removeEventListener("loadstart", onLoop);
    };
  }, [showCustomControls, playbackSrc]);

  useEffect(() => {
    const onFs = () => {
      setIsFullscreen(document.fullscreenElement === playerRootRef.current);
    };
    document.addEventListener("fullscreenchange", onFs);
    return () => document.removeEventListener("fullscreenchange", onFs);
  }, []);

  const togglePlay = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) void video.play().catch(() => undefined);
    else video.pause();
  }, []);

  const seekTo = useCallback((time: number) => {
    const video = videoRef.current;
    if (!video) return;
    const max = Number.isFinite(video.duration) ? video.duration : time;
    video.currentTime = Math.min(Math.max(0, time), max || 0);
    setCurrentTime(video.currentTime);
  }, []);

  const stepFrame = useCallback(
    (dir: -1 | 1) => {
      const video = videoRef.current;
      if (!video) return;
      video.pause();
      seekTo((video.currentTime || 0) + dir * FRAME_STEP);
    },
    [seekTo]
  );

  const toggleMute = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    video.muted = !video.muted;
    setMuted(video.muted);
  }, []);

  const setVolumeLevel = useCallback((value: number) => {
    const video = videoRef.current;
    if (!video) return;
    const next = Math.min(1, Math.max(0, value));
    video.volume = next;
    video.muted = next === 0;
    setVolume(next);
    setMuted(video.muted);
  }, []);

  const setRate = useCallback((rate: number) => {
    const video = videoRef.current;
    if (!video) return;
    video.playbackRate = rate;
    setPlaybackRate(rate);
  }, []);

  const toggleLoop = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    video.loop = !video.loop;
    setLoop(video.loop);
  }, []);

  const toggleFullscreen = useCallback(() => {
    const root = playerRootRef.current;
    if (!root) return;
    if (document.fullscreenElement === root) {
      void document.exitFullscreen?.();
    } else {
      void root.requestFullscreen?.();
    }
  }, []);

  const onPlayerKeyDown = useCallback(
    (e: ReactKeyboardEvent<HTMLDivElement>) => {
      if (!showCustomControls) return;
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "SELECT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable)
      ) {
        return;
      }

      if (e.key === " " || e.key === "k" || e.key === "K") {
        e.preventDefault();
        togglePlay();
        return;
      }
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        seekTo(currentTime - 5);
        return;
      }
      if (e.key === "ArrowRight") {
        e.preventDefault();
        seekTo(currentTime + 5);
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setVolumeLevel(volume + 0.05);
        return;
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setVolumeLevel(volume - 0.05);
        return;
      }
      if (e.key === "m" || e.key === "M") {
        e.preventDefault();
        toggleMute();
        return;
      }
      if (e.key === "f" || e.key === "F") {
        e.preventDefault();
        toggleFullscreen();
        return;
      }
      if (e.key === "," || e.key === "<") {
        e.preventDefault();
        stepFrame(-1);
        return;
      }
      if (e.key === "." || e.key === ">") {
        e.preventDefault();
        stepFrame(1);
      }
    },
    [
      showCustomControls,
      togglePlay,
      seekTo,
      currentTime,
      setVolumeLevel,
      volume,
      toggleMute,
      toggleFullscreen,
      stepFrame,
    ]
  );

  if (isShowcase && !isGenerating) {
    return <ShowcaseDemoPlayer />;
  }

  return (
    <div className="video-player-block">
      {title && !isGenerating && (
        <p className="video-player-title">{title}</p>
      )}
      <div
        ref={playerRootRef}
        className={`rtas-player${isFullscreen ? " rtas-player--fullscreen" : ""}`}
        tabIndex={showCustomControls ? 0 : undefined}
        onKeyDown={onPlayerKeyDown}
        aria-label={title ? `Video player: ${title}` : "Video player"}
      >
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
              ref={videoRef}
              src={playbackSrc}
              playsInline
              preload="metadata"
              className="player-video"
              onError={handleVideoError}
              onClick={togglePlay}
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

        {showCustomControls ? (
          <div className="rtas-player__bar" role="group" aria-label="Playback controls">
            <div className="rtas-player__timeline-row">
              <span className="rtas-player__time" aria-hidden>
                {formatPlayerTime(currentTime)}
              </span>
              <input
                type="range"
                className="rtas-player__scrubber"
                min={0}
                max={duration || 0}
                step={0.01}
                value={Math.min(currentTime, duration || 0)}
                aria-label="Seek"
                aria-valuetext={`${formatPlayerTime(currentTime)} of ${formatPlayerTime(duration)}`}
                onChange={(e) => seekTo(Number(e.target.value))}
              />
              <span className="rtas-player__time" aria-hidden>
                {formatPlayerTime(duration)}
              </span>
            </div>

            <div className="rtas-player__controls">
              <div className="rtas-player__cluster">
                <button
                  type="button"
                  className="rtas-player__btn"
                  onClick={togglePlay}
                  aria-label={playing ? "Pause" : "Play"}
                >
                  {playing ? "❚❚" : "▶"}
                </button>
                <button
                  type="button"
                  className="rtas-player__btn"
                  onClick={() => stepFrame(-1)}
                  aria-label="Previous frame"
                  title="Step back 1 frame"
                >
                  ‹‹
                </button>
                <button
                  type="button"
                  className="rtas-player__btn"
                  onClick={() => stepFrame(1)}
                  aria-label="Next frame"
                  title="Step forward 1 frame"
                >
                  ››
                </button>
              </div>

              <div className="rtas-player__cluster rtas-player__cluster--volume">
                <button
                  type="button"
                  className="rtas-player__btn"
                  onClick={toggleMute}
                  aria-label={muted || volume === 0 ? "Unmute" : "Mute"}
                >
                  {muted || volume === 0 ? "Mute" : "Vol"}
                </button>
                <input
                  type="range"
                  className="rtas-player__volume"
                  min={0}
                  max={1}
                  step={0.01}
                  value={muted ? 0 : volume}
                  aria-label="Volume"
                  onChange={(e) => setVolumeLevel(Number(e.target.value))}
                />
              </div>

              <div className="rtas-player__cluster">
                <label className="rtas-player__speed">
                  <span className="rtas-player__sr-only">Playback speed</span>
                  <select
                    value={playbackRate}
                    aria-label="Playback speed"
                    onChange={(e) => setRate(Number(e.target.value))}
                  >
                    {PLAYBACK_RATES.map((rate) => (
                      <option key={rate} value={rate}>
                        {rate === 1 ? "1×" : `${rate}×`}
                      </option>
                    ))}
                  </select>
                </label>

                <button
                  type="button"
                  className={`rtas-player__btn${loop ? " rtas-player__btn--active" : ""}`}
                  onClick={toggleLoop}
                  aria-pressed={loop}
                  aria-label={loop ? "Disable loop" : "Enable loop"}
                >
                  Loop
                </button>

                <button
                  type="button"
                  className="rtas-player__btn"
                  onClick={toggleFullscreen}
                  aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
                >
                  {isFullscreen ? "⤢" : "⛶"}
                </button>
              </div>
            </div>
          </div>
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


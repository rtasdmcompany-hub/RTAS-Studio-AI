"use client";

import type { GeneratedVideo } from "@rtas/shared";
import type { UserProfile } from "@rtas/shared";

type Props = {
  videos: GeneratedVideo[];
  activeVideoId: string | null | undefined;
  profile: UserProfile;
  disabled?: boolean;
  onSelect: (video: GeneratedVideo) => void;
  onShare?: (video: GeneratedVideo) => void;
};

export function StudioVideoCarousel({
  videos,
  activeVideoId,
  profile,
  disabled = false,
  onSelect,
  onShare,
}: Props) {
  return (
    <section className="shashka-carousel" aria-label="Your videos">
      <h2 className="shashka-carousel__label">Your Videos</h2>
      <div className="shashka-carousel__track" role="list">
        {videos.length === 0 ? (
          <p className="shashka-carousel__empty">No videos yet</p>
        ) : (
          videos.map((v) => {
            const active = activeVideoId === v.id;
            const isPreview =
              !profile.subscriptionActive || v.previewOnly;
            const canShare =
              v.status === "ready" && Boolean(v.videoUrl) && Boolean(onShare);
            return (
              <div
                key={v.id}
                role="listitem"
                className={`shashka-carousel__item${active ? " shashka-carousel__item--active" : ""}`}
              >
                <button
                  type="button"
                  className={`shashka-carousel__vinyl${active ? " shashka-carousel__vinyl--active" : ""}`}
                  onClick={() => onSelect(v)}
                  disabled={disabled}
                  aria-pressed={active}
                >
                  <span className="shashka-carousel__disc" aria-hidden>
                    <span className="shashka-carousel__disc-groove" />
                    <span className="shashka-carousel__disc-label">
                      {v.title.slice(0, 2).toUpperCase()}
                    </span>
                  </span>
                  <span className="shashka-carousel__meta">
                    <span className="shashka-carousel__title">{v.title}</span>
                    <span
                      className={`shashka-carousel__badge${isPreview ? "" : " shashka-carousel__badge--premium"}`}
                    >
                      {isPreview ? "Preview" : v.isPublic ? "Public" : "Premium"}
                    </span>
                  </span>
                </button>
                {canShare && onShare ? (
                  <button
                    type="button"
                    className="shashka-carousel__share-btn"
                    onClick={() => onShare(v)}
                    disabled={disabled}
                    aria-label={`Share ${v.title}`}
                  >
                    Share Video
                  </button>
                ) : null}
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}

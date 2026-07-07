"use client";

import Link from "next/link";
import {
  isActivePipelineStatus,
  pipelineProgressPercent,
  type PipelineStatus,
} from "@rtas/shared";
import type { GalleryDisplayItem } from "@/lib/gallery-display";

type Props = {
  item: GalleryDisplayItem;
  variant?: "grid" | "compact";
  active?: boolean;
  disabled?: boolean;
  subscriptionActive?: boolean;
  onSelect?: (item: GalleryDisplayItem) => void;
  onShare?: (item: GalleryDisplayItem) => void;
  onDelete?: (id: string) => void;
};

function isProcessing(status: PipelineStatus): boolean {
  return isActivePipelineStatus(status);
}

export function AssetVideoCard({
  item,
  variant = "grid",
  active = false,
  disabled = false,
  subscriptionActive = false,
  onSelect,
  onShare,
  onDelete,
}: Props) {
  const processing = isProcessing(item.pipelineStatus);
  const failed = item.pipelineStatus === "failed";
  const completed = item.pipelineStatus === "completed" && Boolean(item.videoUrl);
  const isPreview = item.previewOnly || !subscriptionActive;
  const progress = pipelineProgressPercent(item);
  const canShare = completed && Boolean(onShare);
  const canSelect = completed && Boolean(onSelect);
  const compact = variant === "compact";

  const handlePrimaryAction = () => {
    if (!canSelect || disabled) return;
    onSelect?.(item);
  };

  return (
    <article
      className={[
        "asset-card",
        compact ? "asset-card--compact" : "asset-card--grid",
        active ? "asset-card--active" : "",
        processing ? "asset-card--processing" : "",
        failed ? "asset-card--failed" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      data-status={item.pipelineStatus}
    >
      <div className="asset-card__media">
        {processing ? (
          <div className="asset-card__shimmer" aria-hidden>
            <span className="asset-card__shimmer-wave" />
            <span className="asset-card__shimmer-ring" />
          </div>
        ) : completed && item.videoUrl ? (
          <video
            className="asset-card__preview"
            src={item.videoUrl}
            muted
            playsInline
            preload="none"
            aria-label={`Preview of ${item.title}`}
          />
        ) : (
          <div className="asset-card__placeholder" aria-hidden>
            <span>{item.title.slice(0, 2).toUpperCase()}</span>
          </div>
        )}

        {processing ? (
          <span className="asset-card__badge asset-card__badge--processing">
            Processing… {progress}%
          </span>
        ) : failed ? (
          <span className="asset-card__badge asset-card__badge--failed">
            Failed
          </span>
        ) : (
          <span
            className={`asset-card__badge${isPreview ? "" : " asset-card__badge--premium"}`}
          >
            {isPreview ? "Preview" : item.isPublic ? "Public" : "Premium"}
          </span>
        )}
      </div>

      <div className="asset-card__body">
        <h3 className="asset-card__title" title={item.title}>
          {item.title}
        </h3>
        <p className="asset-card__meta">
          {item.durationSeconds}s · {new Date(item.createdAt).toLocaleDateString()}
        </p>

        {failed ? (
          <p className="asset-card__alert" role="status">
            {item.errorMessage?.trim() || "This render could not be completed."}
          </p>
        ) : processing ? (
          <p className="asset-card__status-line">{item.statusLabel}</p>
        ) : null}

        <div className="asset-card__actions">
          {canSelect ? (
            <button
              type="button"
              className="asset-card__btn asset-card__btn--primary"
              onClick={handlePrimaryAction}
              disabled={disabled}
            >
              Play
            </button>
          ) : processing ? (
            <button type="button" className="asset-card__btn" disabled>
              Rendering…
            </button>
          ) : null}

          {failed ? (
            <>
              <Link
                href="/studio"
                className="asset-card__btn asset-card__btn--ghost"
              >
                Retry in Studio
              </Link>
              {onDelete ? (
                <button
                  type="button"
                  className="asset-card__btn asset-card__btn--danger"
                  onClick={() => onDelete(item.id)}
                >
                  Delete
                </button>
              ) : null}
            </>
          ) : null}

          {canShare ? (
            <button
              type="button"
              className="asset-card__btn asset-card__btn--ghost"
              onClick={() => onShare?.(item)}
              disabled={disabled}
            >
              Share
            </button>
          ) : null}
        </div>
      </div>
    </article>
  );
}

export function AssetGallerySkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="asset-gallery__grid" aria-busy="true" aria-label="Loading videos">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="asset-card asset-card--grid asset-card--skeleton">
          <div className="asset-card__media asset-card__shimmer">
            <span className="asset-card__shimmer-wave" />
          </div>
          <div className="asset-card__body">
            <div className="asset-card__skel-line asset-card__skel-line--title" />
            <div className="asset-card__skel-line asset-card__skel-line--meta" />
          </div>
        </div>
      ))}
    </div>
  );
}

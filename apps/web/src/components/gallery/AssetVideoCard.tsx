"use client";

import { memo, useCallback } from "react";
import {
  isActivePipelineStatus,
  pipelineProgressPercent,
  type PipelineStatus,
} from "@rtas/shared";
import { Badge, Button, ButtonLink, SkeletonBar } from "@rtas/ui";
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

function AssetVideoCardComponent({
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

  const handlePrimaryAction = useCallback(() => {
    if (!canSelect || disabled) return;
    onSelect?.(item);
  }, [canSelect, disabled, item, onSelect]);

  const handleShare = useCallback(() => {
    onShare?.(item);
  }, [item, onShare]);

  const handleDelete = useCallback(() => {
    onDelete?.(item.id);
  }, [item.id, onDelete]);

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
          <Badge
            variant="warning"
            className="asset-card__badge asset-card__badge--processing"
          >
            Processing… {progress}%
          </Badge>
        ) : failed ? (
          <Badge
            variant="danger"
            className="asset-card__badge asset-card__badge--failed"
          >
            Failed
          </Badge>
        ) : (
          <Badge
            variant={isPreview ? "default" : "accent"}
            className={`asset-card__badge${isPreview ? "" : " asset-card__badge--premium"}`}
          >
            {isPreview ? "Preview" : item.isPublic ? "Public" : "Premium"}
          </Badge>
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
            <Button
              type="button"
              variant="asset-primary"
              onClick={handlePrimaryAction}
              disabled={disabled}
            >
              Play
            </Button>
          ) : processing ? (
            <Button type="button" variant="asset-ghost" disabled>
              Rendering…
            </Button>
          ) : null}

          {failed ? (
            <>
              <ButtonLink href="/studio" variant="asset-ghost">
                Retry in Studio
              </ButtonLink>
              {onDelete ? (
                <Button
                  type="button"
                  variant="asset-danger"
                  onClick={handleDelete}
                >
                  Delete
                </Button>
              ) : null}
            </>
          ) : null}

          {canShare ? (
            <Button
              type="button"
              variant="asset-ghost"
              onClick={handleShare}
              disabled={disabled}
            >
              Share
            </Button>
          ) : null}
        </div>
      </div>
    </article>
  );
}

export const AssetVideoCard = memo(AssetVideoCardComponent);

export function AssetGallerySkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="asset-gallery__grid" aria-busy="true" aria-label="Loading videos">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="asset-card asset-card--grid asset-card--skeleton">
          <div className="asset-card__media">
            <SkeletonBar className="h-full w-full min-h-[8rem] rounded-none" />
          </div>
          <div className="asset-card__body">
            <SkeletonBar className="asset-card__skel-line asset-card__skel-line--title h-4 w-3/4" />
            <SkeletonBar className="asset-card__skel-line asset-card__skel-line--meta mt-2 h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

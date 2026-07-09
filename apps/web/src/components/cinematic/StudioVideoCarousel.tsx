"use client";

import { memo, useMemo } from "react";
import type { UserProfile } from "@rtas/shared";
import type { GalleryDisplayItem } from "@/lib/gallery-display";
import { Button, EmptyState } from "@rtas/ui";
import { AssetVideoCard } from "@/components/gallery/AssetVideoCard";

type Props = {
  items: GalleryDisplayItem[];
  activeVideoId: string | null | undefined;
  profile: UserProfile | null;
  disabled?: boolean;
  hasMore?: boolean;
  loadingMore?: boolean;
  onSelect: (item: GalleryDisplayItem) => void;
  onShare?: (item: GalleryDisplayItem) => void;
  onLoadMore?: () => void;
  onRefresh?: () => void;
};

function StudioVideoCarouselComponent({
  items,
  activeVideoId,
  profile,
  disabled = false,
  hasMore = false,
  loadingMore = false,
  onSelect,
  onShare,
  onLoadMore,
  onRefresh,
}: Props) {
  const processingCount = useMemo(
    () =>
      items.filter((item) =>
        ["queued", "generating_chunks", "compiling_media", "processing"].includes(
          item.pipelineStatus ?? ""
        )
      ).length,
    [items]
  );

  const subscriptionActive = Boolean(profile?.subscriptionActive);

  return (
    <section className="shashka-carousel" aria-label="Generation history">
      <div className="shashka-carousel__header">
        <h2 className="shashka-carousel__label">Your Videos</h2>
        {processingCount > 0 ? (
          <span className="shashka-carousel__badge" aria-live="polite">
            {processingCount} rendering
          </span>
        ) : null}
      </div>

      <div className="shashka-carousel__track asset-gallery__carousel-track" role="list">
        {items.length === 0 ? (
          <EmptyState
            className="studio-gallery-empty"
            icon="🎬"
            title="No renders yet"
            description="Your finished videos will land here with live status. Generate once to fill this shelf."
            action={
              onRefresh ? (
                <Button variant="ghost" size="sm" onClick={onRefresh}>
                  Refresh
                </Button>
              ) : undefined
            }
          />
        ) : (
          items.map((item) => (
            <div
              key={item.id}
              role="listitem"
              className={`shashka-carousel__item${activeVideoId === item.id ? " shashka-carousel__item--active" : ""}`}
            >
              <AssetVideoCard
                item={item}
                variant="compact"
                active={activeVideoId === item.id}
                disabled={disabled}
                subscriptionActive={subscriptionActive}
                onSelect={onSelect}
                onShare={onShare}
              />
            </div>
          ))
        )}
      </div>

      {hasMore && onLoadMore ? (
        <div className="shashka-carousel__more">
          <Button
            variant="secondary"
            size="sm"
            loading={loadingMore}
            loadingLabel="Loading…"
            onClick={onLoadMore}
          >
            Load more
          </Button>
        </div>
      ) : null}
    </section>
  );
}

export const StudioVideoCarousel = memo(StudioVideoCarouselComponent);

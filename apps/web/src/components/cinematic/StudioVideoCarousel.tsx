"use client";

import type { UserProfile } from "@rtas/shared";
import type { GalleryDisplayItem } from "@/lib/gallery-display";
import { AssetVideoCard } from "@/components/gallery/AssetVideoCard";

type Props = {
  items: GalleryDisplayItem[];
  activeVideoId: string | null | undefined;
  profile: UserProfile | null;
  disabled?: boolean;
  onSelect: (item: GalleryDisplayItem) => void;
  onShare?: (item: GalleryDisplayItem) => void;
};

export function StudioVideoCarousel({
  items,
  activeVideoId,
  profile,
  disabled = false,
  onSelect,
  onShare,
}: Props) {
  return (
    <section className="shashka-carousel" aria-label="Your videos">
      <h2 className="shashka-carousel__label">Your Videos</h2>
      <div className="shashka-carousel__track asset-gallery__carousel-track" role="list">
        {items.length === 0 ? (
          <p className="shashka-carousel__empty">No videos yet</p>
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
                subscriptionActive={Boolean(profile?.subscriptionActive)}
                onSelect={onSelect}
                onShare={onShare}
              />
            </div>
          ))
        )}
      </div>
    </section>
  );
}

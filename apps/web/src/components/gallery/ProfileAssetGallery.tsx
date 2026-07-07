"use client";

import { useCallback } from "react";
import { useUserVideoGallery } from "@/hooks/useUserVideoGallery";
import {
  AssetGallerySkeleton,
  AssetVideoCard,
} from "@/components/gallery/AssetVideoCard";

type Props = {
  userId: string;
};

export function ProfileAssetGallery({ userId }: Props) {
  const gallery = useUserVideoGallery(userId, {
    pollActive: true,
  });

  const handleDelete = useCallback(
    async (jobId: string) => {
      const res = await fetch(`/api/user/videos/${jobId}`, { method: "DELETE" });
      if (res.ok) {
        gallery.removeItem(jobId);
        return;
      }
      const body = (await res.json().catch(() => ({}))) as { error?: string };
      window.alert(body.error ?? "Could not delete this render.");
    },
    [gallery.removeItem]
  );

  return (
    <section className="profile-asset-gallery" aria-labelledby="profile-gallery-heading">
      <div className="profile-asset-gallery__header">
        <h2 id="profile-gallery-heading">Your renders</h2>
        <p className="profile-asset-gallery__sub">
          Server-backed gallery — active jobs refresh automatically.
        </p>
      </div>

      {gallery.error ? (
        <p className="profile-asset-gallery__error" role="alert">
          {gallery.error}{" "}
          <button type="button" className="asset-card__btn asset-card__btn--ghost" onClick={() => void gallery.refresh()}>
            Retry
          </button>
        </p>
      ) : null}

      {gallery.loading && gallery.items.length === 0 ? (
        <AssetGallerySkeleton count={6} />
      ) : gallery.items.length === 0 ? (
        <p className="profile-asset-gallery__empty">
          No renders yet.{" "}
          <a href="/studio">Create your first video in Studio</a>.
        </p>
      ) : (
        <>
          <div className="asset-gallery__grid">
            {gallery.items.map((item) => (
              <AssetVideoCard
                key={item.id}
                item={item}
                variant="grid"
                onDelete={handleDelete}
              />
            ))}
          </div>

          {gallery.hasMore ? (
            <div className="profile-asset-gallery__more">
              <button
                type="button"
                className="btn-secondary"
                disabled={gallery.loadingMore}
                onClick={() => void gallery.loadMore()}
              >
                {gallery.loadingMore ? "Loading…" : "Load more renders"}
              </button>
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}

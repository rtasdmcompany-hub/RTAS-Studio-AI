"use client";

import { useCallback, useState } from "react";
import { Alert, Button, EmptyState } from "@rtas/ui";
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
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleDelete = useCallback(
    async (jobId: string) => {
      setDeleteError(null);
      const res = await fetch(`/api/user/videos/${jobId}`, { method: "DELETE" });
      if (res.ok) {
        gallery.removeItem(jobId);
        return;
      }
      const body = (await res.json().catch(() => ({}))) as { error?: string };
      setDeleteError(body.error ?? "Could not delete this render. Please try again.");
    },
    [gallery.removeItem]
  );

  return (
    <section className="profile-asset-gallery" aria-labelledby="profile-gallery-heading">
      <div className="profile-asset-gallery__header">
        <h2 id="profile-gallery-heading">Your library</h2>
        <p className="profile-asset-gallery__sub">
          Finished and active renders — updates automatically while jobs run.
        </p>
      </div>

      {deleteError ? (
        <Alert
          variant="error"
          message={deleteError}
          onDismiss={() => setDeleteError(null)}
          className="profile-asset-gallery__notice"
        />
      ) : null}

      {gallery.error ? (
        <Alert
          variant="error"
          title="Couldn't load your renders"
          message={gallery.error}
          className="profile-asset-gallery__notice"
        >
          <Button
            variant="ui-ghost"
            size="sm"
            onClick={() => void gallery.refresh()}
            className="profile-asset-gallery__retry"
          >
            Retry
          </Button>
        </Alert>
      ) : null}

      {gallery.loading && gallery.items.length === 0 ? (
        <AssetGallerySkeleton count={6} />
      ) : gallery.items.length === 0 && !gallery.error ? (
        <EmptyState
          icon="🎬"
          title="No renders yet"
          description="Finished videos land here with live status. Create once in Studio to fill your library."
          actionLabel="Create your first video →"
          actionHref="/studio"
        />
      ) : gallery.items.length > 0 ? (
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
              <Button
                variant="secondary"
                loading={gallery.loadingMore}
                loadingLabel="Loading…"
                onClick={() => void gallery.loadMore()}
              >
                Load more renders
              </Button>
            </div>
          ) : null}
        </>
      ) : null}
    </section>
  );
}

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  DEFAULT_VIDEO_PAGE_SIZE,
  isActivePipelineStatus,
  type UserVideoAsset,
} from "@rtas/shared";

export type UserVideoGalleryState = {
  items: UserVideoAsset[];
  loading: boolean;
  loadingMore: boolean;
  error: string | null;
  hasMore: boolean;
  refresh: () => Promise<void>;
  loadMore: () => Promise<void>;
  removeItem: (id: string) => void;
};

type VideoPageResponse = {
  items: UserVideoAsset[];
  nextCursor: string | null;
  hasMore: boolean;
};

const POLL_MS = 5_000;

export type UseUserVideoGalleryOptions = {
  pageSize?: number;
  pollActive?: boolean;
  /** API path for paginated videos (default `/api/user/videos`) */
  apiPath?: string;
};

export function useUserVideoGallery(
  userId: string | null | undefined,
  options?: UseUserVideoGalleryOptions
): UserVideoGalleryState {
  const pageSize = options?.pageSize ?? DEFAULT_VIDEO_PAGE_SIZE;
  const pollActive = options?.pollActive ?? true;
  const apiPath = options?.apiPath ?? "/api/user/videos";

  const [items, setItems] = useState<UserVideoAsset[]>([]);
  const [loading, setLoading] = useState(Boolean(userId));
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);

  const fetchGenRef = useRef(0);
  const nextCursorRef = useRef<string | null>(null);
  const userIdRef = useRef(userId);
  userIdRef.current = userId;

  // Boolean primitive — stable across polls that don't change active-job presence,
  // so the interval effect does not restart on every items array identity change.
  const hasActiveJobs = useMemo(
    () => items.some((item) => isActivePipelineStatus(item.pipelineStatus)),
    [items]
  );

  const applyPage = useCallback(
    (data: VideoPageResponse, append: boolean) => {
      setItems((prev) => (append ? [...prev, ...data.items] : data.items));
      setNextCursor(data.nextCursor);
      nextCursorRef.current = data.nextCursor;
      setHasMore(data.hasMore);
    },
    []
  );

  const fetchPage = useCallback(
    async (cursor: string | null, append: boolean) => {
      const uid = userIdRef.current;
      if (!uid) return;

      const gen = ++fetchGenRef.current;
      const params = new URLSearchParams({ userId: uid, limit: String(pageSize) });
      if (cursor) params.set("cursor", cursor);

      const res = await fetch(`${apiPath}?${params.toString()}`);
      if (!res.ok) throw new Error(`Gallery fetch failed (${res.status})`);
      const data = (await res.json()) as VideoPageResponse;
      if (gen !== fetchGenRef.current) return;
      applyPage(data, append);
    },
    [apiPath, applyPage, pageSize]
  );

  const refresh = useCallback(async () => {
    if (!userIdRef.current) return;
    setLoading(true);
    setError(null);
    try {
      await fetchPage(null, false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load videos");
    } finally {
      setLoading(false);
    }
  }, [fetchPage]);

  const loadMore = useCallback(async () => {
    const cursor = nextCursorRef.current;
    if (!userIdRef.current || !cursor || loadingMore) return;
    setLoadingMore(true);
    setError(null);
    try {
      await fetchPage(cursor, true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load more");
    } finally {
      setLoadingMore(false);
    }
  }, [fetchPage, loadingMore]);

  const removeItem = useCallback((id: string) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
  }, []);

  useEffect(() => {
    if (!userId) {
      setItems([]);
      setLoading(false);
      setHasMore(false);
      setNextCursor(null);
      return;
    }
    void refresh();
  }, [userId, refresh]);

  useEffect(() => {
    if (!pollActive || !userId || !hasActiveJobs) return;

    const timer = window.setInterval(() => {
      if (document.visibilityState === "hidden") return;
      void fetchPage(null, false).catch(() => {});
    }, POLL_MS);

    return () => window.clearInterval(timer);
  }, [pollActive, userId, hasActiveJobs, fetchPage]);

  return useMemo(
    () => ({
      items,
      loading,
      loadingMore,
      error,
      hasMore,
      refresh,
      loadMore,
      removeItem,
    }),
    [items, loading, loadingMore, error, hasMore, refresh, loadMore, removeItem]
  );
}

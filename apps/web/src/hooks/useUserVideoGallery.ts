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

export function useUserVideoGallery(
  userId: string | null | undefined,
  options?: { pageSize?: number; pollActive?: boolean }
): UserVideoGalleryState {
  const pageSize = options?.pageSize ?? DEFAULT_VIDEO_PAGE_SIZE;
  const pollActive = options?.pollActive ?? true;

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

  const applyPage = useCallback(
    (data: VideoPageResponse, append: boolean) => {
      setItems((prev) => (append ? [...prev, ...data.items] : data.items));
      setNextCursor(data.nextCursor);
      nextCursorRef.current = data.nextCursor;
      setHasMore(data.hasMore);
      setError(null);
    },
    []
  );

  const fetchPage = useCallback(
    async (cursor: string | null, append: boolean) => {
      const uid = userIdRef.current;
      if (!uid) return;

      const generation = ++fetchGenRef.current;
      const params = new URLSearchParams({
        limit: String(pageSize),
      });
      if (cursor) params.set("cursor", cursor);

      try {
        const res = await fetch(`/api/user/videos?${params.toString()}`, {
          cache: "no-store",
        });
        if (generation !== fetchGenRef.current) return;

        if (!res.ok) {
          const body = (await res.json().catch(() => ({}))) as { error?: string };
          throw new Error(body.error ?? `Failed to load videos (${res.status})`);
        }

        const data = (await res.json()) as VideoPageResponse;
        if (generation !== fetchGenRef.current) return;
        applyPage(data, append);
      } catch (err) {
        if (generation !== fetchGenRef.current) return;
        setError(err instanceof Error ? err.message : "Failed to load videos");
      }
    },
    [applyPage, pageSize]
  );

  const refresh = useCallback(async () => {
    if (!userIdRef.current) return;
    setLoading(true);
    await fetchPage(null, false);
    setLoading(false);
  }, [fetchPage]);

  const loadMore = useCallback(async () => {
    const cursor = nextCursorRef.current;
    if (!userIdRef.current || !cursor || loadingMore) return;
    setLoadingMore(true);
    await fetchPage(cursor, true);
    setLoadingMore(false);
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
      nextCursorRef.current = null;
      return;
    }

    let cancelled = false;
    setLoading(true);
    void (async () => {
      await fetchPage(null, false);
      if (!cancelled) setLoading(false);
    })();

    return () => {
      cancelled = true;
      fetchGenRef.current += 1;
    };
  }, [userId, fetchPage]);

  const activeKey = useMemo(
    () =>
      items
        .filter((item) => isActivePipelineStatus(item.pipelineStatus))
        .map((item) => item.id)
        .join(","),
    [items]
  );

  useEffect(() => {
    if (!pollActive || !activeKey || !userId) return;

    const timer = window.setInterval(() => {
      void fetchPage(null, false);
    }, POLL_MS);

    return () => window.clearInterval(timer);
  }, [activeKey, pollActive, userId, fetchPage]);

  return {
    items,
    loading,
    loadingMore,
    error,
    hasMore,
    refresh,
    loadMore,
    removeItem,
  };
}

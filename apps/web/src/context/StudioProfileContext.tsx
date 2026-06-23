"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useSession } from "next-auth/react";
import type { UserProfile } from "@rtas/shared";
import type { PaidPlanType } from "@rtas/shared";
import {
  activatePlan,
  applyCreditExpiry,
  capCreditsForTier,
  loadProfile,
  mergeServerProfile,
  saveProfile,
} from "@/lib/store";

export type StudioMetricsState = {
  renderingQueues: number;
  concurrentTracks: number;
  maxConcurrentGenerations: number;
  videoGenerationCredits: number;
  recentJobs: Array<{
    id: string;
    status: string;
    prompt: string | null;
    inputImageUrl: string | null;
    generatedVideoUrl: string | null;
    durationSeconds: number;
    creditsCharged: number;
    createdAt: string;
  }>;
};

type StudioProfileContextValue = {
  profile: UserProfile | null;
  studioMetrics: StudioMetricsState | null;
  generationLimitReached: boolean;
  generationLimitMessage: string | null;
  setProfile: (profile: UserProfile) => void;
  refreshProfile: () => void;
  syncFromServer: (userId: string) => Promise<UserProfile | null>;
  activatePremium: () => UserProfile;
};

const StudioProfileContext = createContext<StudioProfileContextValue | null>(
  null
);

const GENERATION_LIMIT_MESSAGE =
  "Maximum concurrent rendering tracks reached. Please wait for active videos to complete.";

const CREDITS_LIMIT_MESSAGE =
  "Insufficient generation credits. Please upgrade your studio plan.";

function applySessionToProfile(
  base: UserProfile,
  session: { user?: { id?: string; email?: string | null; name?: string | null } }
): UserProfile {
  if (!session.user?.id) return base;
  return {
    ...base,
    id: session.user.id,
    email: session.user.email ?? base.email,
    name: session.user.name ?? base.name,
  };
}

export function StudioProfileProvider({ children }: { children: ReactNode }) {
  const { data: session, status } = useSession();
  const [profile, setProfileState] = useState<UserProfile | null>(null);
  const [studioMetrics, setStudioMetrics] = useState<StudioMetricsState | null>(
    null
  );

  const refreshProfile = useCallback(() => {
    setProfileState(loadProfile());
  }, []);

  const syncFromServer = useCallback(async (userId: string): Promise<UserProfile | null> => {
    try {
      const res = await fetch(`/api/user/subscription?userId=${encodeURIComponent(userId)}`);
      if (!res.ok) return null;
      const server = (await res.json()) as {
        tier: UserProfile["tier"];
        subscriptionActive: boolean;
        credits: number;
        creditsExpireAt: string | null;
        subscriptionRenewsAt: string | null;
        paymentProvider?: UserProfile["paymentProvider"];
        freeTrialUsed: boolean;
        hasUsedFreeTrial: boolean;
        studioMetrics: StudioMetricsState;
      };
      const local = loadProfile();
      const merged = mergeServerProfile(local, {
        ...local,
        tier: server.tier,
        subscriptionActive: server.subscriptionActive,
        credits: server.credits,
        creditsExpireAt: server.creditsExpireAt,
        subscriptionRenewsAt: server.subscriptionRenewsAt,
        paymentProvider: server.paymentProvider,
        freeTrialUsed: server.freeTrialUsed,
        hasUsedFreeTrial: server.hasUsedFreeTrial,
      });
      const capped = capCreditsForTier(merged);
      saveProfile(capped);
      setProfileState(capped);
      setStudioMetrics(server.studioMetrics);
      return capped;
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    if (status === "loading") return;

    let loaded = applyCreditExpiry(loadProfile());
    if (session?.user) {
      loaded = applySessionToProfile(loaded, session);
    }
    saveProfile(loaded);
    setProfileState(loaded);
    setStudioMetrics(null);
    void syncFromServer(loaded.id);

    const params = new URLSearchParams(window.location.search);
    if (params.get("activated") === "1" || params.get("payment") === "success") {
      const rawPlan = params.get("plan");
      const plan: PaidPlanType =
        rawPlan === "standard" || rawPlan === "premium" ? rawPlan : "standard";
      const p = activatePlan(loaded, plan);
      saveProfile(p);
      setProfileState(p);
      void syncFromServer(p.id);
      void fetch("/api/admin/fal-funding/refresh", { method: "POST" }).catch(() => {});
    }
  }, [session, status, syncFromServer]);

  const setProfile = useCallback((p: UserProfile) => {
    saveProfile(p);
    setProfileState(p);
  }, []);

  const activatePremium = useCallback(() => {
    const base = loadProfile();
    const p = activatePlan(base, "premium");
    saveProfile(p);
    setProfileState(p);
    return p;
  }, []);

  const value = useMemo(() => {
    const concurrentTracks =
      studioMetrics?.concurrentTracks ?? studioMetrics?.renderingQueues ?? 0;
    const maxTracks = studioMetrics?.maxConcurrentGenerations ?? 3;
    const credits =
      studioMetrics?.videoGenerationCredits ?? profile?.credits ?? 0;

    const atConcurrentLimit = !!studioMetrics && concurrentTracks >= maxTracks;
    const outOfCredits = credits <= 0;

    return {
      profile,
      studioMetrics,
      generationLimitReached: atConcurrentLimit || outOfCredits,
      generationLimitMessage: atConcurrentLimit
        ? GENERATION_LIMIT_MESSAGE
        : outOfCredits
          ? CREDITS_LIMIT_MESSAGE
          : null,
      setProfile,
      refreshProfile,
      syncFromServer,
      activatePremium,
    };
  }, [
    profile,
    studioMetrics,
    setProfile,
    refreshProfile,
    syncFromServer,
    activatePremium,
  ]);

  return (
    <StudioProfileContext.Provider value={value}>
      {children}
    </StudioProfileContext.Provider>
  );
}

export function useStudioProfile() {
  const ctx = useContext(StudioProfileContext);
  if (!ctx) {
    throw new Error("useStudioProfile must be used within StudioProfileProvider");
  }
  return ctx;
}

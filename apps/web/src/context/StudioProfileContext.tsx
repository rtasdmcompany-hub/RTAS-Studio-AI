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

type StudioProfileContextValue = {
  profile: UserProfile | null;
  setProfile: (profile: UserProfile) => void;
  refreshProfile: () => void;
  syncFromServer: (userId: string) => Promise<UserProfile | null>;
  activatePremium: () => UserProfile;
};

const StudioProfileContext = createContext<StudioProfileContextValue | null>(
  null
);

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

  const refreshProfile = useCallback(() => {
    setProfileState(loadProfile());
  }, []);

  const syncFromServer = useCallback(async (userId: string): Promise<UserProfile | null> => {
    try {
      const res = await fetch(`/api/user/subscription?userId=${encodeURIComponent(userId)}`);
      if (!res.ok) return null;
      const server = await res.json();
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
    void syncFromServer(loaded.id);

    const params = new URLSearchParams(window.location.search);
    if (params.get("activated") === "1" || params.get("payment") === "success") {
      const rawPlan = params.get("plan");
      const plan: PaidPlanType =
        rawPlan === "tester" || rawPlan === "standard" || rawPlan === "premium"
          ? rawPlan
          : "standard";
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

  const value = useMemo(
    () => ({
      profile,
      setProfile,
      refreshProfile,
      syncFromServer,
      activatePremium,
    }),
    [profile, setProfile, refreshProfile, syncFromServer, activatePremium]
  );

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

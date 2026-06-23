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
import {
  activatePlan,
  applyCreditExpiry,
  loadProfile,
  mergeServerProfile,
  saveProfile,
} from "@/lib/store";

export type TesterSubscriptionState = {
  id: string;
  allowedSeconds: number;
  secondsUsed: number;
  remainingSeconds: number;
  endDate: string;
  isActive: boolean;
};

type OmniReachProfileContextValue = {
  profile: UserProfile | null;
  testerSubscription: TesterSubscriptionState | null;
  testerLimitReached: boolean;
  testerLimitMessage: string | null;
  setProfile: (profile: UserProfile) => void;
  refreshProfile: () => void;
  syncFromServer: (userId: string) => Promise<UserProfile | null>;
};

const OmniReachProfileContext =
  createContext<OmniReachProfileContextValue | null>(null);

const PUBLISH_LOCK_MESSAGE =
  "Action locked. Review Tester Session metrics.";

export function OmniReachProfileProvider({ children }: { children: ReactNode }) {
  const { data: session, status } = useSession();
  const [profile, setProfileState] = useState<UserProfile | null>(null);
  const [testerSubscription, setTesterSubscription] =
    useState<TesterSubscriptionState | null>(null);

  const refreshProfile = useCallback(() => {
    setProfileState(loadProfile());
  }, []);

  const syncFromServer = useCallback(async (userId: string) => {
    try {
      const res = await fetch(
        `/api/user/subscription?userId=${encodeURIComponent(userId)}`
      );
      if (!res.ok) return null;
      const server = (await res.json()) as {
        tier: UserProfile["tier"];
        subscriptionActive: boolean;
        paymentProvider?: UserProfile["paymentProvider"];
        testerSubscription: TesterSubscriptionState | null;
      };
      const local = loadProfile();
      const merged = mergeServerProfile(local, {
        ...local,
        tier: server.tier,
        subscriptionActive: server.subscriptionActive,
        paymentProvider: server.paymentProvider,
      });
      saveProfile(merged);
      setProfileState(merged);
      setTesterSubscription(server.testerSubscription);
      return merged;
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    if (status === "loading") return;

    let loaded = applyCreditExpiry(loadProfile());
    if (session?.user?.id) {
      loaded = {
        ...loaded,
        id: session.user.id,
        email: session.user.email ?? loaded.email,
        name: session.user.name ?? loaded.name,
      };
    }
    saveProfile(loaded);
    setProfileState(loaded);
    setTesterSubscription(null);
    void syncFromServer(loaded.id);

    const params = new URLSearchParams(window.location.search);
    if (params.get("activated") === "1" || params.get("payment") === "success") {
      const p = activatePlan(loaded, "tester");
      saveProfile(p);
      setProfileState(p);
      void syncFromServer(p.id);
    }
  }, [session, status, syncFromServer]);

  const setProfile = useCallback((p: UserProfile) => {
    saveProfile(p);
    setProfileState(p);
  }, []);

  const value = useMemo(
    () => ({
      profile,
      testerSubscription,
      testerLimitReached:
        profile?.tier === "tester" &&
        !!testerSubscription &&
        (!testerSubscription.isActive ||
          testerSubscription.remainingSeconds <= 0),
      testerLimitMessage:
        profile?.tier === "tester" &&
        testerSubscription &&
        (!testerSubscription.isActive ||
          testerSubscription.remainingSeconds <= 0)
          ? PUBLISH_LOCK_MESSAGE
          : null,
      setProfile,
      refreshProfile,
      syncFromServer,
    }),
    [profile, testerSubscription, setProfile, refreshProfile, syncFromServer]
  );

  return (
    <OmniReachProfileContext.Provider value={value}>
      {children}
    </OmniReachProfileContext.Provider>
  );
}

export function useOmniReachProfile() {
  const ctx = useContext(OmniReachProfileContext);
  if (!ctx) {
    throw new Error(
      "useOmniReachProfile must be used within OmniReachProfileProvider"
    );
  }
  return ctx;
}

"use client";

import { SessionProvider } from "next-auth/react";
import type { ReactNode } from "react";
import { AnalyticsProvider } from "@/components/analytics/AnalyticsProvider";
import { PromotionAttributionTracker } from "@/components/promotions/PromotionAttributionTracker";
import { StudioProfileProvider } from "@/context/StudioProfileContext";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <SessionProvider>
      <StudioProfileProvider>
        <AnalyticsProvider>
          <PromotionAttributionTracker />
          {children}
        </AnalyticsProvider>
      </StudioProfileProvider>
    </SessionProvider>
  );
}

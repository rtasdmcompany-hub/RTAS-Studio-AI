"use client";

import { SessionProvider } from "next-auth/react";
import { Suspense, type ReactNode } from "react";
import { AnalyticsProvider } from "@/components/analytics/AnalyticsProvider";
import { PromotionAttributionTracker } from "@/components/promotions/PromotionAttributionTracker";
import { StudioProfileProvider } from "@/context/StudioProfileContext";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <SessionProvider>
      <StudioProfileProvider>
        <AnalyticsProvider>
          <Suspense fallback={null}>
            <PromotionAttributionTracker />
          </Suspense>
          {children}
        </AnalyticsProvider>
      </StudioProfileProvider>
    </SessionProvider>
  );
}

"use client";

import { SessionProvider } from "next-auth/react";
import type { ReactNode } from "react";
import { OmniReachProfileProvider } from "@/context/OmniReachProfileContext";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <SessionProvider>
      <OmniReachProfileProvider>{children}</OmniReachProfileProvider>
    </SessionProvider>
  );
}

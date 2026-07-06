"use client";

import { SessionProvider } from "next-auth/react";
import type { ReactNode } from "react";
import { StudioProfileProvider } from "@/context/StudioProfileContext";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <SessionProvider>
      <StudioProfileProvider>{children}</StudioProfileProvider>
    </SessionProvider>
  );
}

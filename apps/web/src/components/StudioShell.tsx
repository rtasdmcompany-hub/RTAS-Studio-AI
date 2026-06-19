"use client";

import { SiteHeader } from "@/components/SiteHeader";
import { StudioProfileProvider } from "@/context/StudioProfileContext";
import { LiveChatWidget } from "@/components/marketing/LiveChatWidget";
import { BackToTop } from "@/components/marketing/BackToTop";
import { CreditsPill } from "./CreditsPill";
import { StudioClient } from "./StudioClient";

export function StudioShell() {
  return (
    <StudioProfileProvider>
      <div className="studio-shell--unified">
        <SiteHeader
          className="rtas-header--studio"
          actionsSlot={<CreditsPill />}
          authVariant="studio"
        />
        <StudioClient />
        <BackToTop />
        <LiveChatWidget />
      </div>
    </StudioProfileProvider>
  );
}

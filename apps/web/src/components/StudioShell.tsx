"use client";

import { LiveChatWidget } from "@/components/marketing/LiveChatWidget";
import { BackToTop } from "@/components/marketing/BackToTop";
import { StudioClient } from "./StudioClient";

export function StudioShell() {
  return (
    <div className="studio-shell--unified">
      <StudioClient />
      <BackToTop />
      <LiveChatWidget />
    </div>
  );
}

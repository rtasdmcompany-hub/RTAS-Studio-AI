"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { signOut, useSession } from "next-auth/react";

type Mode = "signup" | "login" | "check-email";

export function AuthFlowGuard({ mode }: { mode: Mode }) {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status !== "authenticated") return;

    if (mode === "signup" || mode === "check-email") {
      void signOut({ redirect: false });
      return;
    }

    if (mode === "login" && session?.user?.emailVerified !== false) {
      router.replace("/studio");
    }
  }, [mode, router, session?.user?.emailVerified, status]);

  return null;
}
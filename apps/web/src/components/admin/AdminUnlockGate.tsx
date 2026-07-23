"use client";

import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Alert, Button } from "@rtas/ui";

const ADMIN_KEY = "rtas_admin_secret";

export function useAdminSecret() {
  const [secret, setSecret] = useState("");
  const [stored, setStored] = useState("");

  useEffect(() => {
    const s = sessionStorage.getItem(ADMIN_KEY);
    if (s) setStored(s);
  }, []);

  function unlock(e: FormEvent) {
    e.preventDefault();
    if (!secret.trim()) return;
    sessionStorage.setItem(ADMIN_KEY, secret.trim());
    setStored(secret.trim());
  }

  function clear() {
    sessionStorage.removeItem(ADMIN_KEY);
    setStored("");
    setSecret("");
  }

  return { secret, setSecret, stored, unlock, clear };
}

export function AdminUnlockGate({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: (adminSecret: string, clear: () => void) => ReactNode;
}) {
  const { secret, setSecret, stored, unlock, clear } = useAdminSecret();

  if (!stored) {
    return (
      <div className="mx-auto max-w-md p-6">
        <h1 className="text-xl text-zinc-100">{title}</h1>
        <p className="mt-2 text-sm text-ds-text-muted">{description}</p>
        <form className="mt-6 space-y-3" onSubmit={unlock}>
          <input
            type="password"
            className="w-full rounded-md border border-ds-border-subtle bg-ds-surface-glass px-3 py-2 text-zinc-100"
            placeholder="RTAS_ADMIN_SECRET"
            value={secret}
            onChange={(e) => setSecret(e.target.value)}
            autoComplete="current-password"
          />
          <Button type="submit" variant="primary" className="w-full">
            Unlock
          </Button>
        </form>
      </div>
    );
  }

  return <>{children(stored, clear)}</>;
}

export function AdminLoadError({ message }: { message: string | null }) {
  if (!message) return null;
  return <Alert variant="error" message={message} />;
}

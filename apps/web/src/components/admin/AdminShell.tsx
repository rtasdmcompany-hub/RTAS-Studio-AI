"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Alert, Button, Card } from "@rtas/ui";

export const ADMIN_SECRET_KEY = "rtas_admin_secret";

const NAV = [
  { href: "/admin", label: "Ops" },
  { href: "/admin/executive", label: "Executive BI" },
  { href: "/admin/launch", label: "Launch readiness" },
  { href: "/admin/acquisition", label: "Acquisition" },
  { href: "/admin/revenue", label: "RevOps" },
  { href: "/admin/enterprise", label: "Enterprise" },
  { href: "/admin/marketing", label: "Marketing" },
  { href: "/admin/tickets", label: "Tickets" },
];

export function useAdminSecret() {
  const [secret, setSecret] = useState("");
  const [stored, setStored] = useState("");

  useEffect(() => {
    const s = sessionStorage.getItem(ADMIN_SECRET_KEY);
    if (s) setStored(s);
  }, []);

  function unlock(e: FormEvent) {
    e.preventDefault();
    if (!secret.trim()) return;
    sessionStorage.setItem(ADMIN_SECRET_KEY, secret.trim());
    setStored(secret.trim());
  }

  function lock() {
    sessionStorage.removeItem(ADMIN_SECRET_KEY);
    setStored("");
    setSecret("");
  }

  return { secret, setSecret, stored, unlock, lock };
}

export function AdminMetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <Card className="p-4">
      <p className="text-xs uppercase tracking-wide text-ds-text-muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-zinc-100">{value}</p>
      {hint ? <p className="mt-1 text-xs text-ds-text-muted">{hint}</p> : null}
    </Card>
  );
}

export function AdminUnlockGate({
  title,
  description,
  secret,
  setSecret,
  onUnlock,
}: {
  title: string;
  description: string;
  secret: string;
  setSecret: (v: string) => void;
  onUnlock: (e: FormEvent) => void;
}) {
  return (
    <div className="mx-auto max-w-md p-6">
      <h1 className="text-xl text-zinc-100">{title}</h1>
      <p className="mt-2 text-sm text-ds-text-muted">{description}</p>
      <form className="mt-6 space-y-3" onSubmit={onUnlock}>
        <input
          type="password"
          className="w-full rounded-md border border-ds-border-subtle bg-ds-surface-glass px-3 py-2 text-zinc-100"
          placeholder="RTAS_ADMIN_SECRET"
          value={secret}
          onChange={(e) => setSecret(e.target.value)}
        />
        <Button type="submit" variant="primary" className="w-full">
          Unlock
        </Button>
      </form>
    </div>
  );
}

export function AdminNav({ onLock }: { onLock?: () => void }) {
  const pathname = usePathname();
  return (
    <nav className="flex flex-wrap items-center gap-2 text-sm">
      {NAV.map((item) => {
        const active =
          item.href === "/admin"
            ? pathname === "/admin"
            : pathname?.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={
              active
                ? "rounded-md bg-ds-surface-glass px-3 py-1.5 text-zinc-100"
                : "rounded-md px-3 py-1.5 text-ds-text-muted hover:text-zinc-100"
            }
          >
            {item.label}
          </Link>
        );
      })}
      {onLock ? (
        <Button variant="ghost" className="ml-auto" onClick={onLock}>
          Lock
        </Button>
      ) : null}
    </nav>
  );
}

export function AdminPageShell({
  title,
  subtitle,
  stored,
  secret,
  setSecret,
  unlock,
  lock,
  busy,
  error,
  onRefresh,
  children,
}: {
  title: string;
  subtitle: string;
  stored: string;
  secret: string;
  setSecret: (v: string) => void;
  unlock: (e: FormEvent) => void;
  lock: () => void;
  busy?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  children: ReactNode;
}) {
  if (!stored) {
    return (
      <AdminUnlockGate
        title={`${title} access`}
        description="Enter your RTAS admin secret. Same secret as /admin operations."
        secret={secret}
        setSecret={setSecret}
        onUnlock={unlock}
      />
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <AdminNav onLock={lock} />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl text-zinc-100">{title}</h1>
          <p className="text-sm text-ds-text-muted">{subtitle}</p>
        </div>
        {onRefresh ? (
          <Button variant="ghost" disabled={busy} onClick={onRefresh}>
            Refresh
          </Button>
        ) : null}
      </div>
      {error ? <Alert variant="error" message={error} /> : null}
      {children}
    </div>
  );
}

export function formatUsd(n: number | null | undefined): string {
  if (n === null || n === undefined) return "N/A";
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

export function formatPct(n: number | null | undefined): string {
  if (n === null || n === undefined) return "N/A";
  return `${n}%`;
}

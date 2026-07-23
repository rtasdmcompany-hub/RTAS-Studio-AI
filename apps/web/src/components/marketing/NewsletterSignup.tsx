"use client";

import { useState } from "react";
import { Button } from "@rtas/ui";

export function NewsletterSignup() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      const res = await fetch("/api/newsletter/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name }),
      });
      const json = (await res.json()) as { ok?: boolean; message?: string; error?: string };
      if (!res.ok || !json.ok) {
        throw new Error(json.error ?? "Subscribe failed.");
      }
      setMessage(json.message ?? "Subscribed.");
      setEmail("");
      setName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Subscribe failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="flex max-w-lg flex-col gap-3 sm:flex-row sm:items-end" onSubmit={onSubmit}>
      <label className="flex-1 text-sm">
        <span className="text-ds-text-muted">Name (optional)</span>
        <input
          className="mt-1 w-full rounded-md border border-white/10 bg-black/20 px-3 py-2 text-ds-text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          autoComplete="name"
        />
      </label>
      <label className="flex-[1.4] text-sm">
        <span className="text-ds-text-muted">Email</span>
        <input
          required
          type="email"
          className="mt-1 w-full rounded-md border border-white/10 bg-black/20 px-3 py-2 text-ds-text"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
        />
      </label>
      <Button type="submit" variant="primary" disabled={busy}>
        {busy ? "…" : "Subscribe"}
      </Button>
      {message ? <p className="basis-full text-sm text-emerald-300">{message}</p> : null}
      {error ? <p className="basis-full text-sm text-red-300">{error}</p> : null}
    </form>
  );
}

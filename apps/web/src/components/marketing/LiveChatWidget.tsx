"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  buildWelcomeMessage,
  CHAT_QUICK_REPLIES,
  type ChatMessage,
} from "@/lib/live-chat";
import { SITE_SUPPORT_EMAIL } from "@/lib/site-links";

const SUPPORT_EMAIL = SITE_SUPPORT_EMAIL;

function formatBotText(text: string): ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return part.split("\n").map((line, j, arr) => (
      <span key={`${i}-${j}`}>
        {line}
        {j < arr.length - 1 ? <br /> : null}
      </span>
    ));
  });
}

export function LiveChatWidget() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: buildWelcomeMessage() },
  ]);
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  useEffect(() => {
    if (open) {
      window.setTimeout(() => inputRef.current?.focus(), 120);
    }
  }, [open]);

  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, busy, open]);

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || busy) return;

    const userMsg: ChatMessage = { role: "user", content: trimmed };
    const nextHistory = [...messages, userMsg];
    setMessages(nextHistory);
    setInput("");
    setBusy(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          history: nextHistory.slice(-12),
        }),
      });
      const data = (await res.json().catch(() => ({}))) as { reply?: string; error?: string };
      const reply =
        data.reply ??
        (res.ok
          ? `Sorry, I couldn't answer that. Please email ${SUPPORT_EMAIL}.`
          : data.error ?? `Chat is temporarily unavailable. Please email ${SUPPORT_EMAIL}.`);

      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Connection issue — please email ${SUPPORT_EMAIL} and our team will help.`,
        },
      ]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      {open ? (
        <div
          id="rtas-live-chat-panel"
          className="rtas-live-chat"
          role="dialog"
          aria-label="Live chat support"
          aria-modal="false"
        >
          <header className="rtas-live-chat__header">
            <div>
              <p className="rtas-live-chat__title">RTAS Support</p>
              <p className="rtas-live-chat__status">
                <span className="rtas-live-chat__dot" aria-hidden />
                Online — instant replies
              </p>
            </div>
            <button
              type="button"
              className="rtas-live-chat__close"
              aria-label="Close chat"
              onClick={() => setOpen(false)}
            >
              ✕
            </button>
          </header>

          <div ref={listRef} className="rtas-live-chat__messages">
            {messages.map((msg, idx) => (
              <div
                key={`${msg.role}-${idx}`}
                className={
                  msg.role === "user"
                    ? "rtas-live-chat__bubble rtas-live-chat__bubble--user"
                    : "rtas-live-chat__bubble rtas-live-chat__bubble--bot"
                }
              >
                {msg.role === "assistant" ? formatBotText(msg.content) : msg.content}
              </div>
            ))}
            {busy ? (
              <div className="rtas-live-chat__typing" aria-live="polite">
                <span />
                <span />
                <span />
              </div>
            ) : null}
          </div>

          {messages.length <= 2 ? (
            <div className="rtas-live-chat__quick">
              {CHAT_QUICK_REPLIES.map((q) => (
                <button
                  key={q}
                  type="button"
                  className="rtas-live-chat__quick-btn"
                  disabled={busy}
                  onClick={() => void sendMessage(q)}
                >
                  {q}
                </button>
              ))}
            </div>
          ) : null}

          <form
            className="rtas-live-chat__form"
            onSubmit={(e) => {
              e.preventDefault();
              void sendMessage(input);
            }}
          >
            <input
              ref={inputRef}
              type="text"
              className="rtas-live-chat__input"
              placeholder="Type your question…"
              value={input}
              disabled={busy}
              maxLength={2000}
              aria-label="Chat message"
            />
            <button
              type="submit"
              className="rtas-live-chat__send"
              disabled={busy || !input.trim()}
              aria-label="Send message"
            >
              ↑
            </button>
          </form>

          <footer className="rtas-live-chat__footer">
            <a href={`mailto:${SUPPORT_EMAIL}`}>Email {SUPPORT_EMAIL}</a>
            <span> · </span>
            <Link href="/pricing">Pricing</Link>
          </footer>
        </div>
      ) : null}

      <button
        type="button"
        className={`rtas-live-chat-fab${open ? " rtas-live-chat-fab--open" : ""}`}
        aria-expanded={open}
        aria-controls="rtas-live-chat-panel"
        aria-label={open ? "Close live chat" : "Open live chat"}
        onClick={() => setOpen((v) => !v)}
      >
        {open ? "✕" : "💬"}
      </button>
    </>
  );
}

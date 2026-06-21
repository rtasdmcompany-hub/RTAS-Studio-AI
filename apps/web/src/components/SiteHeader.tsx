"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { RtasHeaderBrand } from "@/components/RtasHeaderBrand";
import { AuthHeaderActions } from "@/components/auth/AuthHeaderActions";

const NAV = [
  { href: "/studio", label: "Studio" },
  { href: "/how-to-use", label: "How to use" },
  { href: "/pricing", label: "Pricing" },
  { href: "/about", label: "About" },
  { href: "/terms", label: "Legal" },
] as const;

type Props = {
  /** Studio-only slot (e.g. credits pill) shown before auth actions */
  actionsSlot?: ReactNode;
  authVariant?: "landing" | "studio";
  className?: string;
};

function isNavActive(pathname: string, href: string): boolean {
  if (href === "/studio") return pathname.startsWith("/studio");
  if (href === "/how-to-use") return pathname.startsWith("/how-to-use");
  if (href === "/pricing") return pathname === "/pricing";
  if (href === "/about") return pathname === "/about";
  if (href === "/terms") {
    return pathname.startsWith("/terms") || pathname.startsWith("/privacy");
  }
  return false;
}

export function SiteHeader({ actionsSlot, authVariant = "landing", className }: Props) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenuOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [menuOpen]);

  const headerClass = [
    "rtas-header",
    className,
    menuOpen ? "rtas-header--menu-open" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <header className={headerClass}>
      <div className="rtas-header__inner">
        <RtasHeaderBrand logoSize={28} />

        <nav className="rtas-header__nav" aria-label="Primary">
          {NAV.map(({ href, label }) => {
            const active = isNavActive(pathname, href);
            return (
              <Link
                key={href}
                href={href}
                className={
                  active ? "rtas-header__link rtas-header__link--active" : "rtas-header__link"
                }
              >
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="rtas-header__actions rtas-header__actions--desktop">
          {actionsSlot}
          <AuthHeaderActions variant={authVariant} />
          <Link href="/studio" className="rtas-btn-lavender rtas-header__cta">
            Start creating
          </Link>
        </div>

        <button
          type="button"
          className="rtas-header__menu-btn"
          aria-expanded={menuOpen}
          aria-controls="rtas-mobile-nav"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? "✕" : "☰"}
        </button>
      </div>

      {menuOpen ? (
        <nav id="rtas-mobile-nav" className="rtas-header__mobile-menu" aria-label="Mobile">
          {NAV.map(({ href, label }) => {
            const active = isNavActive(pathname, href);
            return (
              <Link
                key={href}
                href={href}
                className={
                  active
                    ? "rtas-header__mobile-link rtas-header__mobile-link--active"
                    : "rtas-header__mobile-link"
                }
                onClick={() => setMenuOpen(false)}
              >
                {label}
              </Link>
            );
          })}
          <div className="rtas-header__mobile-actions">
            {actionsSlot}
            <AuthHeaderActions variant={authVariant} />
            <Link
              href="/studio"
              className="rtas-btn-lavender rtas-header__mobile-cta"
              onClick={() => setMenuOpen(false)}
            >
              Start creating
            </Link>
          </div>
        </nav>
      ) : null}
    </header>
  );
}

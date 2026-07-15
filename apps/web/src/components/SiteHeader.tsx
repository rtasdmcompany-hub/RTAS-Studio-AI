"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { ButtonLink } from "@rtas/ui";
import { RtasHeaderBrand } from "@/components/RtasHeaderBrand";
import { AuthHeaderActions } from "@/components/auth/AuthHeaderActions";
import { HeaderNotifications } from "@/components/HeaderNotifications";

/** Single commercial primary nav — same on every route */
const SITE_NAV = [
  { href: "/studio", label: "Studio" },
  { href: "/profile", label: "Dashboard" },
  { href: "/showcase", label: "Showcase" },
  { href: "/features", label: "Features" },
  { href: "/pricing", label: "Pricing" },
  { href: "/docs", label: "Documentation" },
  { href: "/help", label: "Help" },
] as const;

type Props = {
  /** Credits / upgrade slot shown before notifications + auth */
  actionsSlot?: ReactNode;
  authVariant?: "landing" | "studio";
  className?: string;
};

function isNavActive(pathname: string, href: string): boolean {
  if (href === "/studio") return pathname.startsWith("/studio");
  if (href === "/profile") return pathname.startsWith("/profile");
  if (href === "/showcase") return pathname.startsWith("/showcase");
  if (href === "/features") return pathname.startsWith("/features");
  if (href === "/pricing") return pathname === "/pricing";
  if (href === "/docs") {
    return pathname.startsWith("/docs") || pathname.startsWith("/how-to-use");
  }
  if (href === "/help") {
    return (
      pathname.startsWith("/help") ||
      pathname.startsWith("/feedback") ||
      pathname.startsWith("/support")
    );
  }
  return false;
}

export function SiteHeader({ actionsSlot, authVariant = "landing", className }: Props) {
  const pathname = usePathname() ?? "";
  const [menuOpen, setMenuOpen] = useState(false);
  const isStudio = authVariant === "studio" || pathname.startsWith("/studio");

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
    "rtas-header--premium",
    isStudio ? "rtas-header--studio" : "",
    className,
    menuOpen ? "rtas-header--menu-open" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <header className={headerClass}>
      <div className="rtas-header__inner">
        <RtasHeaderBrand href="/" logoSize={40} />

        <nav className="rtas-header__nav" aria-label="Primary">
          {SITE_NAV.map(({ href, label }) => {
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
          <HeaderNotifications />
          <AuthHeaderActions variant={authVariant} />
          {!isStudio ? (
            <ButtonLink href="/studio" variant="lavender" className="rtas-header__cta">
              Start creating
            </ButtonLink>
          ) : null}
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
          {SITE_NAV.map(({ href, label }) => {
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
            <HeaderNotifications />
            <AuthHeaderActions variant={authVariant} />
            {!isStudio ? (
              <ButtonLink
                href="/studio"
                variant="lavender"
                className="rtas-header__mobile-cta"
                onClick={() => setMenuOpen(false)}
              >
                Start creating
              </ButtonLink>
            ) : null}
          </div>
        </nav>
      ) : null}
    </header>
  );
}

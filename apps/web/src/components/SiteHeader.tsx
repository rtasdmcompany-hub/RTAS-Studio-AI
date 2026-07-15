"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { ButtonLink } from "@rtas/ui";
import { RtasHeaderBrand } from "@/components/RtasHeaderBrand";
import { AuthHeaderActions } from "@/components/auth/AuthHeaderActions";
import { HeaderNotifications } from "@/components/HeaderNotifications";

/** Single commercial primary nav — same on every route */
const SITE_NAV: {
  href: string;
  label: string;
  priority: 1 | 2 | 3;
  fullLabel?: string;
}[] = [
  { href: "/studio", label: "Studio", priority: 1 },
  { href: "/profile", label: "Dashboard", priority: 1 },
  { href: "/showcase", label: "Showcase", priority: 2 },
  { href: "/features", label: "Features", priority: 2 },
  { href: "/pricing", label: "Pricing", priority: 1 },
  { href: "/docs", label: "Docs", priority: 3, fullLabel: "Documentation" },
  { href: "/help", label: "Help", priority: 3 },
];

type Density = "full" | "comfortable" | "compact" | "tight";

type Props = {
  /** Credits / upgrade slot shown before notifications + auth */
  actionsSlot?: ReactNode;
  authVariant?: "landing" | "studio";
  className?: string;
};

function densityFromWidth(width: number): Density {
  if (width < 1180) return "tight";
  if (width < 1366) return "compact";
  if (width < 1600) return "comfortable";
  return "full";
}

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
  const [density, setDensity] = useState<Density>("full");
  const [useDrawerNav, setUseDrawerNav] = useState(false);
  const headerRef = useRef<HTMLElement>(null);
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

  useEffect(() => {
    const measure = () => {
      const w = window.innerWidth;
      setDensity(densityFromWidth(w));
      // Desktop drawer below 1280 — prevents right-side clipping with credits + profile
      setUseDrawerNav(w < 1280);
    };
    measure();
    window.addEventListener("resize", measure, { passive: true });
    return () => window.removeEventListener("resize", measure);
  }, []);

  const logoSize = density === "full" ? 40 : density === "comfortable" ? 36 : 32;
  const showDesktopNav = !useDrawerNav;
  const maxNavPriority =
    density === "full" ? 3 : density === "comfortable" ? 3 : density === "compact" ? 2 : 1;
  const visibleNav = SITE_NAV.filter((item) => item.priority <= maxNavPriority);
  const overflowNav = SITE_NAV.filter((item) => item.priority > maxNavPriority);

  const headerClass = [
    "rtas-header",
    "rtas-header--premium",
    isStudio ? "rtas-header--studio" : "",
    `rtas-header--density-${density}`,
    useDrawerNav ? "rtas-header--drawer-nav" : "",
    className,
    menuOpen ? "rtas-header--menu-open" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <header className={headerClass} ref={headerRef}>
      <div className="rtas-header__inner">
        <RtasHeaderBrand href="/" logoSize={logoSize} />

        {showDesktopNav ? (
          <nav className="rtas-header__nav" aria-label="Primary">
            {visibleNav.map(({ href, label, fullLabel }) => {
              const active = isNavActive(pathname, href);
              const text = density === "full" && fullLabel ? fullLabel : label;
              return (
                <Link
                  key={href}
                  href={href}
                  className={
                    active ? "rtas-header__link rtas-header__link--active" : "rtas-header__link"
                  }
                >
                  {text}
                </Link>
              );
            })}
            {overflowNav.length > 0 ? (
              <details className="rtas-header__more">
                <summary className="rtas-header__link rtas-header__more-summary">More</summary>
                <div className="rtas-header__more-menu" role="menu">
                  {overflowNav.map(({ href, label, fullLabel }) => {
                    const active = isNavActive(pathname, href);
                    return (
                      <Link
                        key={href}
                        href={href}
                        role="menuitem"
                        className={
                          active
                            ? "rtas-header__more-link rtas-header__more-link--active"
                            : "rtas-header__more-link"
                        }
                      >
                        {fullLabel ?? label}
                      </Link>
                    );
                  })}
                </div>
              </details>
            ) : null}
          </nav>
        ) : null}

        <div className="rtas-header__actions rtas-header__actions--desktop">
          {actionsSlot}
          <HeaderNotifications />
          <AuthHeaderActions variant={authVariant} />
          {!isStudio && density !== "tight" ? (
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
          {SITE_NAV.map(({ href, label, fullLabel }) => {
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
                {fullLabel ?? label}
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

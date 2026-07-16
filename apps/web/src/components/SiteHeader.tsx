"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { ButtonLink } from "@rtas/ui";
import { RtasHeaderBrand } from "@/components/RtasHeaderBrand";
import { AuthHeaderActions } from "@/components/auth/AuthHeaderActions";
import { HeaderNotifications } from "@/components/HeaderNotifications";

/** Primary commercial nav — priority controls progressive disclosure */
const SITE_NAV: {
  href: string;
  label: string;
  priority: 1 | 2 | 3;
  fullLabel?: string;
}[] = [
  { href: "/studio", label: "Studio", priority: 1 },
  { href: "/profile", label: "Dashboard", priority: 1 },
  { href: "/showcase", label: "Showcase", priority: 1 },
  { href: "/pricing", label: "Pricing", priority: 1 },
  { href: "/features", label: "Features", priority: 2 },
  { href: "/docs", label: "Docs", priority: 2, fullLabel: "Documentation" },
  { href: "/help", label: "Help", priority: 3 },
];

type Density = "full" | "comfortable" | "compact" | "mobile";

type Props = {
  actionsSlot?: ReactNode;
  authVariant?: "landing" | "studio";
  className?: string;
};

function densityFromWidth(width: number): Density {
  if (width < 900) return "mobile";
  if (width < 1180) return "compact";
  if (width < 1440) return "comfortable";
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
  const [density, setDensity] = useState<Density>("compact");
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
    const measure = () => setDensity(densityFromWidth(window.innerWidth));
    measure();
    window.addEventListener("resize", measure, { passive: true });
    return () => window.removeEventListener("resize", measure);
  }, []);

  const isMobile = density === "mobile";
  const logoSize = density === "full" ? 36 : 32;
  const maxNavPriority =
    density === "full" ? 3 : density === "comfortable" ? 2 : density === "compact" ? 1 : 0;
  const visibleNav = isMobile
    ? []
    : SITE_NAV.filter((item) => item.priority <= maxNavPriority);
  const overflowNav = isMobile
    ? SITE_NAV
    : SITE_NAV.filter((item) => item.priority > maxNavPriority);

  const headerClass = [
    "rtas-header",
    "rtas-header--premium",
    "rtas-header--fixed",
    isStudio ? "rtas-header--studio" : "",
    `rtas-header--density-${density}`,
    isMobile ? "rtas-header--mobile" : "",
    className,
    menuOpen ? "rtas-header--menu-open" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <header className={headerClass}>
      <div className="rtas-header__inner">
        <RtasHeaderBrand href="/" logoSize={logoSize} />

        {!isMobile ? (
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

        <div className="rtas-header__spacer" aria-hidden />

        {!isMobile ? (
          <div className="rtas-header__actions rtas-header__actions--desktop">
            {actionsSlot}
            <HeaderNotifications />
            <AuthHeaderActions variant={authVariant} />
            {!isStudio && density === "full" ? (
              <ButtonLink href="/studio" variant="lavender" className="rtas-header__cta">
                Start creating
              </ButtonLink>
            ) : null}
          </div>
        ) : null}

        {isMobile ? (
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
        ) : null}
      </div>

      {menuOpen && isMobile ? (
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

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { ButtonLink } from "@rtas/ui";
import { RtasHeaderBrand } from "@/components/RtasHeaderBrand";
import { AuthHeaderActions } from "@/components/auth/AuthHeaderActions";
import { HeaderNotifications } from "@/components/HeaderNotifications";

/** Commercial primary nav — same on every route */
const SITE_NAV: {
  href: string;
  label: string;
  /** 1 = always on mid+ desktop, 2 = wide, 3 = full / menu */
  priority: 1 | 2 | 3;
  fullLabel?: string;
}[] = [
  { href: "/studio", label: "Studio", priority: 1 },
  { href: "/profile", label: "Dashboard", priority: 1 },
  { href: "/pricing", label: "Pricing", priority: 1 },
  { href: "/showcase", label: "Showcase", priority: 2 },
  { href: "/features", label: "Features", priority: 2 },
  { href: "/docs", label: "Docs", priority: 3, fullLabel: "Documentation" },
  { href: "/help", label: "Help", priority: 3 },
];

type Density = "full" | "comfortable" | "compact" | "tight";

type Props = {
  actionsSlot?: ReactNode;
  authVariant?: "landing" | "studio";
  className?: string;
};

function densityFromWidth(width: number): Density {
  if (width < 900) return "tight";
  if (width < 1200) return "compact";
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
  const [mounted, setMounted] = useState(false);
  const isStudio = authVariant === "studio" || pathname.startsWith("/studio");

  useEffect(() => {
    setMounted(true);
    const measure = () => setDensity(densityFromWidth(window.innerWidth));
    measure();
    window.addEventListener("resize", measure, { passive: true });
    return () => window.removeEventListener("resize", measure);
  }, []);

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

  const logoSize = density === "full" ? 36 : density === "comfortable" ? 34 : 32;
  const maxInlinePriority =
    density === "full" ? 3 : density === "comfortable" ? 2 : density === "compact" ? 1 : 0;
  const showInlineNav = mounted && maxInlinePriority > 0;
  const inlineNav = SITE_NAV.filter((item) => item.priority <= maxInlinePriority);
  const menuOnlyNav = SITE_NAV.filter((item) => item.priority > maxInlinePriority);
  const showHamburger = !mounted || density !== "full" || menuOnlyNav.length > 0;

  const headerClass = [
    "rtas-header",
    "rtas-header--premium",
    "rtas-header--fixed",
    isStudio ? "rtas-header--studio" : "",
    `rtas-header--density-${density}`,
    className,
    menuOpen ? "rtas-header--menu-open" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <>
      <header className={headerClass}>
        <div className="rtas-header__inner">
          <RtasHeaderBrand href="/" logoSize={logoSize} />

          {showInlineNav ? (
            <nav className="rtas-header__nav" aria-label="Primary">
              {inlineNav.map(({ href, label, fullLabel }) => {
                const active = isNavActive(pathname, href);
                const text = density === "full" && fullLabel ? fullLabel : label;
                return (
                  <Link
                    key={href}
                    href={href}
                    className={
                      active
                        ? "rtas-header__link rtas-header__link--active"
                        : "rtas-header__link"
                    }
                  >
                    {text}
                  </Link>
                );
              })}
            </nav>
          ) : (
            <div className="rtas-header__nav-spacer" aria-hidden />
          )}

          <div className="rtas-header__actions">
            <div className="rtas-header__actions-cluster">
              {actionsSlot}
              <HeaderNotifications />
              <AuthHeaderActions variant={authVariant} />
              {!isStudio && density === "full" ? (
                <ButtonLink href="/studio" variant="lavender" className="rtas-header__cta">
                  Start creating
                </ButtonLink>
              ) : null}
            </div>

            {showHamburger ? (
              <button
                type="button"
                className="rtas-header__menu-btn"
                aria-expanded={menuOpen}
                aria-controls="rtas-mobile-nav"
                aria-label={menuOpen ? "Close menu" : "Open menu"}
                onClick={() => setMenuOpen((open) => !open)}
              >
                <span className="rtas-header__menu-icon" aria-hidden>
                  {menuOpen ? (
                    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                      <path
                        d="M4 4l10 10M14 4L4 14"
                        stroke="currentColor"
                        strokeWidth="1.75"
                        strokeLinecap="round"
                      />
                    </svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                      <path
                        d="M3 5h12M3 9h12M3 13h12"
                        stroke="currentColor"
                        strokeWidth="1.75"
                        strokeLinecap="round"
                      />
                    </svg>
                  )}
                </span>
              </button>
            ) : null}
          </div>
        </div>

        {menuOpen ? (
          <nav id="rtas-mobile-nav" className="rtas-header__mobile-menu" aria-label="Menu">
            {(menuOnlyNav.length > 0 ? menuOnlyNav : SITE_NAV).map(
              ({ href, label, fullLabel }) => {
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
              }
            )}
            {!isStudio ? (
              <div className="rtas-header__mobile-actions">
                <ButtonLink
                  href="/studio"
                  variant="lavender"
                  className="rtas-header__mobile-cta"
                  onClick={() => setMenuOpen(false)}
                >
                  Start creating
                </ButtonLink>
              </div>
            ) : null}
          </nav>
        ) : null}
      </header>
      <div className="rtas-header-spacer" aria-hidden />
    </>
  );
}

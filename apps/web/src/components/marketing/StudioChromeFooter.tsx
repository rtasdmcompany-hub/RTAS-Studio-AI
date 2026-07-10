import Link from "next/link";
import {
  SITE_LEGAL_LINKS,
  SITE_PRODUCT_LINKS,
  SITE_SOCIAL_LINKS,
  SITE_SUPPORT_LINKS,
} from "@/lib/site-links";

const CHROME_LINKS = [
  ...SITE_PRODUCT_LINKS.filter((l) => ["pricing", "docs"].includes(l.id)),
  ...SITE_SUPPORT_LINKS.filter((l) => ["help", "status"].includes(l.id)),
  ...SITE_LEGAL_LINKS.filter((l) => ["privacy", "terms"].includes(l.id)),
  { id: "about", label: "About", href: "/about" },
];

export function StudioChromeFooter() {
  return (
    <footer className="studio-chrome-footer" aria-label="Studio footer">
      <nav className="studio-chrome-footer__nav" aria-label="Company links">
        {CHROME_LINKS.map((link) => (
          <Link key={link.id} href={link.href} className="studio-chrome-footer__link">
            {link.label}
          </Link>
        ))}
      </nav>
      <div className="studio-chrome-footer__social" aria-label="Social media">
        {SITE_SOCIAL_LINKS.slice(0, 6).map((social) => (
          <a
            key={social.id}
            href={social.href}
            className="studio-chrome-footer__social-link"
            target="_blank"
            rel="noopener noreferrer"
            aria-label={social.label}
            title={social.label}
          >
            <span aria-hidden>{social.glyph}</span>
          </a>
        ))}
      </div>
    </footer>
  );
}

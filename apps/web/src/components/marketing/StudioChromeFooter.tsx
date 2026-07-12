import Link from "next/link";
import {
  COPYRIGHT_NOTICE,
  PRODUCT_NAME,
} from "@rtas/shared";
import {
  SITE_COMPANY_LINKS,
  SITE_PRODUCT_LINKS,
  SITE_SOCIAL_LINKS,
  SITE_SUPPORT_EMAIL,
  SITE_SUPPORT_LINKS,
} from "@/lib/site-links";

const RESOURCE_LINKS = [
  { id: "how", label: "How to use", href: "/how-to-use" },
  { id: "showcase", label: "AI Showcase", href: "/showcase" },
  { id: "features", label: "Features", href: "/features" },
  { id: "faq", label: "FAQ", href: "/help/faq" },
  { id: "billing", label: "Billing", href: "/help/billing" },
];

const LEGAL_LINKS = SITE_SUPPORT_LINKS.filter((l) =>
  ["privacy", "terms", "cookies"].includes(l.id)
);

function FooterLink({ href, label }: { href: string; label: string }) {
  if (href.startsWith("http") || href.startsWith("mailto:")) {
    return (
      <a href={href} target={href.startsWith("http") ? "_blank" : undefined} rel="noopener noreferrer">
        {label}
      </a>
    );
  }
  return <Link href={href}>{label}</Link>;
}

/** Full international footer for the Studio shell. */
export function StudioChromeFooter() {
  return (
    <footer className="studio-world-footer" aria-label="Studio footer">
      <div className="studio-world-footer__inner">
        <div className="studio-world-footer__brand">
          <p className="studio-world-footer__product">{PRODUCT_NAME}</p>
          <p className="studio-world-footer__tagline">
            International AI video studio — identity-locked cinema for creators, brands, and teams.
          </p>
          <a className="studio-world-footer__contact" href={`mailto:${SITE_SUPPORT_EMAIL}`}>
            {SITE_SUPPORT_EMAIL}
          </a>
          <div className="studio-world-footer__social" aria-label="Social media">
            {SITE_SOCIAL_LINKS.map((social) => (
              <a
                key={social.id}
                href={social.href}
                className="studio-world-footer__social-link"
                target="_blank"
                rel="noopener noreferrer"
                aria-label={social.label}
                title={social.label}
              >
                <span aria-hidden>{social.glyph}</span>
              </a>
            ))}
          </div>
        </div>

        <div className="studio-world-footer__cols">
          <div className="studio-world-footer__col">
            <h3>Product</h3>
            {SITE_PRODUCT_LINKS.map((link) => (
              <FooterLink key={link.id} href={link.href} label={link.label} />
            ))}
          </div>
          <div className="studio-world-footer__col">
            <h3>Company</h3>
            {SITE_COMPANY_LINKS.map((link) => (
              <FooterLink key={link.id} href={link.href} label={link.label} />
            ))}
          </div>
          <div className="studio-world-footer__col">
            <h3>Resources</h3>
            {RESOURCE_LINKS.map((link) => (
              <FooterLink key={link.id} href={link.href} label={link.label} />
            ))}
          </div>
          <div className="studio-world-footer__col">
            <h3>Legal</h3>
            {LEGAL_LINKS.map((link) => (
              <FooterLink key={link.id} href={link.href} label={link.label} />
            ))}
            <FooterLink href="/support" label="Contact" />
          </div>
        </div>
      </div>
      <div className="studio-world-footer__bottom">
        <p>{COPYRIGHT_NOTICE}</p>
      </div>
    </footer>
  );
}

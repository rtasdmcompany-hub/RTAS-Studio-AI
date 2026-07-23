"use client";

import Link from "next/link";
import { MarketingSubscribeForm } from "@/components/marketing/MarketingSubscribeForm";
import {
  COPYRIGHT_NOTICE,
  PRODUCT_NAME,
} from "@rtas/shared";
import {
  SITE_COMPANY_LINKS,
  SITE_DEVELOPER_LINKS,
  SITE_LEGAL_LINKS,
  SITE_PADDLE_POLICY_LINKS,
  SITE_PRODUCT_LINKS,
  SITE_RESOURCE_LINKS,
  SITE_SOCIAL_LINKS,
  SITE_SUPPORT_EMAIL,
} from "@/lib/site-links";

function FooterLink({
  href,
  label,
  external,
}: {
  href: string;
  label: string;
  external?: boolean;
}) {
  if (external || href.startsWith("http") || href.startsWith("mailto:")) {
    return (
      <a
        href={href}
        target={href.startsWith("http") ? "_blank" : undefined}
        rel="noopener noreferrer"
      >
        {label}
      </a>
    );
  }
  return <Link href={href}>{label}</Link>;
}

type Props = {
  className?: string;
};

/**
 * Single international footer used on Studio and all marketing pages.
 */
export function InternationalSiteFooter({ className = "" }: Props) {
  return (
    <footer
      className={`studio-world-footer${className ? ` ${className}` : ""}`}
      aria-label="Site footer"
    >
      <div className="studio-world-footer__inner">
        <div className="studio-world-footer__brand">
          <p className="studio-world-footer__product">{PRODUCT_NAME}</p>
          <p className="studio-world-footer__tagline">
            International AI video studio — Identity Preservation cinema for creators, brands, and teams.
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

        <div className="studio-world-footer__cols studio-world-footer__cols--five">
          <div className="studio-world-footer__col">
            <h3>Product</h3>
            {SITE_PRODUCT_LINKS.map((link) => (
              <FooterLink
                key={link.id}
                href={link.href}
                label={link.label}
                external={link.external}
              />
            ))}
          </div>
          <div className="studio-world-footer__col">
            <h3>Company</h3>
            {SITE_COMPANY_LINKS.map((link) => (
              <FooterLink
                key={link.id}
                href={link.href}
                label={link.label}
                external={link.external}
              />
            ))}
          </div>
          <div className="studio-world-footer__col">
            <h3>Developers</h3>
            {SITE_DEVELOPER_LINKS.map((link) => (
              <FooterLink
                key={link.id}
                href={link.href}
                label={link.label}
                external={link.external}
              />
            ))}
          </div>
          <div className="studio-world-footer__col">
            <h3>Resources</h3>
            {SITE_RESOURCE_LINKS.map((link) => (
              <FooterLink
                key={link.id}
                href={link.href}
                label={link.label}
                external={link.external}
              />
            ))}
          </div>
          <div className="studio-world-footer__col">
            <h3>Legal</h3>
            {SITE_LEGAL_LINKS.map((link) => (
              <FooterLink
                key={link.id}
                href={link.href}
                label={link.label}
                external={link.external}
              />
            ))}
          </div>
        </div>

        <div className="studio-world-footer__subscribe">
          <MarketingSubscribeForm
            kind="newsletter"
            source="footer"
            compact
            allowKindSelect
            title="Product updates & AI tips"
            description="Email only — no free generation credits implied."
          />
        </div>
      </div>
      <div className="studio-world-footer__bottom">
        <nav
          className="studio-world-footer__policies"
          aria-label="Terms of Service, Privacy Policy, and Refund Policy"
        >
          {SITE_PADDLE_POLICY_LINKS.map((link, index) => (
            <span key={link.id} className="studio-world-footer__policies-item">
              {index > 0 ? (
                <span className="studio-world-footer__policies-sep" aria-hidden>
                  ·
                </span>
              ) : null}
              <FooterLink href={link.href} label={link.label} external={link.external} />
            </span>
          ))}
        </nav>
        <p>{COPYRIGHT_NOTICE}</p>
        <p className="studio-world-footer__muted">
          Premium subscription required for commercial downloads. Watermarked previews are for
          evaluation only.
        </p>
      </div>
    </footer>
  );
}

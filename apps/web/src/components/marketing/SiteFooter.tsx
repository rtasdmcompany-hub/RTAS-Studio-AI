import Link from "next/link";
import Image from "next/image";
import {
  COMPANY_NAME,
  COPYRIGHT_NOTICE,
  GROUP_NAME,
  PRODUCT_NAME,
} from "@rtas/shared";
import {
  FOOTER_BRAND_LOGO_PATHS,
  FOOTER_BRAND_LOGO_SIZE,
} from "@/lib/brand-assets";
import {
  SITE_COMPANY_LINKS,
  SITE_PRODUCT_LINKS,
  SITE_SOCIAL_LINKS,
  SITE_SUPPORT_EMAIL,
  SITE_SUPPORT_LINKS,
} from "@/lib/site-links";

const FOOTER_BRANDS = [
  {
    name: PRODUCT_NAME,
    logo: FOOTER_BRAND_LOGO_PATHS.studioAi,
    alt: `${PRODUCT_NAME} logo`,
    width: FOOTER_BRAND_LOGO_SIZE.width,
    height: FOOTER_BRAND_LOGO_SIZE.height,
  },
  {
    name: COMPANY_NAME,
    logo: FOOTER_BRAND_LOGO_PATHS.digitalMarketing,
    alt: `${COMPANY_NAME} logo`,
    width: FOOTER_BRAND_LOGO_SIZE.width,
    height: FOOTER_BRAND_LOGO_SIZE.height,
  },
  {
    name: GROUP_NAME,
    logo: FOOTER_BRAND_LOGO_PATHS.group,
    alt: `${GROUP_NAME} logo`,
    width: FOOTER_BRAND_LOGO_SIZE.width,
    height: FOOTER_BRAND_LOGO_SIZE.height,
  },
] as const;

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

export function SiteFooter() {
  return (
    <footer className="rtas-footer">
      <div className="rtas-footer__inner">
        <div className="rtas-footer__brand-stack">
          {FOOTER_BRANDS.map((brand) => (
            <div key={brand.name} className="rtas-footer__brand-row">
              <Image
                src={brand.logo}
                alt={brand.alt}
                width={brand.width}
                height={brand.height}
                loading="lazy"
                className="rtas-footer__brand-logo"
              />
              <p className="rtas-footer__brand-name">{brand.name}</p>
            </div>
          ))}
          <p className="rtas-footer__tagline">
            International AI video studio for creators, brands, and teams.
          </p>
        </div>

        <div className="rtas-footer__cols">
          <div className="rtas-footer__col">
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
          <div className="rtas-footer__col">
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
          <div className="rtas-footer__col">
            <h3>Support</h3>
            {SITE_SUPPORT_LINKS.map((link) => (
              <FooterLink
                key={link.id}
                href={link.href}
                label={link.label}
                external={link.external}
              />
            ))}
            <a href={`mailto:${SITE_SUPPORT_EMAIL}`}>{SITE_SUPPORT_EMAIL}</a>
          </div>
        </div>
      </div>

      <div className="rtas-footer__social-row" aria-label="Social media">
        {SITE_SOCIAL_LINKS.map((social) => (
          <a
            key={social.id}
            href={social.href}
            className={`rtas-footer__social rtas-footer__social--${social.id}`}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={social.label}
            title={social.label}
          >
            <span aria-hidden>{social.glyph}</span>
          </a>
        ))}
      </div>

      <div className="rtas-footer__bottom">
        <p>{COPYRIGHT_NOTICE}</p>
        <p className="rtas-footer__muted">
          Premium subscription required for commercial downloads. Watermarked
          previews are for evaluation only.
        </p>
      </div>
    </footer>
  );
}

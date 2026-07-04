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
        </div>

        <div className="rtas-footer__cols">
          <div className="rtas-footer__col">
            <h3>Product</h3>
            <Link href="/studio">Open Studio</Link>
            <Link href="/how-to-use">How to use</Link>
            <Link href="/#features">Features</Link>
            <Link href="/pricing">Pricing</Link>
            <Link href="/profile">Account</Link>
          </div>
          <div className="rtas-footer__col">
            <h3>Legal</h3>
            <Link href="/terms">Terms of Service</Link>
            <Link href="/privacy">Privacy Policy</Link>
            <Link href="/cookies">Cookie Policy</Link>
          </div>
          <div className="rtas-footer__col">
            <h3>Support</h3>
            <Link href="/how-to-use">How to use</Link>
            <a href="mailto:support@rtasdigital.com">support@rtasdigital.com</a>
            <p className="rtas-footer__muted">International AI video studio</p>
          </div>
        </div>
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

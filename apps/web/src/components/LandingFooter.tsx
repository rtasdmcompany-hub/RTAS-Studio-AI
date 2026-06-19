import Link from "next/link";
import { COPYRIGHT_NOTICE, PRODUCT_NAME } from "@rtas/shared";

export function LandingFooter() {
  return (
    <footer className="landing-footer">
      <nav className="landing-footer-nav" aria-label="Legal and product links">
        <Link href="/studio">Studio</Link>
        <Link href="/profile">Profile</Link>
        <Link href="/terms">Terms</Link>
        <Link href="/privacy">Privacy</Link>
      </nav>
      <p className="landing-footer-copy">
        {COPYRIGHT_NOTICE}
      </p>
      <p className="landing-footer-note">
        {PRODUCT_NAME} — proprietary software. Commercial use requires an active Premium
        subscription. Watermarked previews may not be distributed commercially.
      </p>
    </footer>
  );
}

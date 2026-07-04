import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { BrandLogo } from "@/components/BrandLogo";

type Props = {
  href?: string;
  logoSize?: number;
};

export function RtasHeaderBrand({ href = "/", logoSize = 32 }: Props) {
  return (
    <Link href={href} className="rtas-header__brand" aria-label={`${PRODUCT_NAME} home`}>
      <BrandLogo
        width={logoSize}
        height={logoSize}
        variant="icon"
        priority
      />
      <span className="rtas-header__brand-text">
        <span className="rtas-header__wordmark">RTAS</span>
        <span className="rtas-header__product">STUDIO AI</span>
      </span>
    </Link>
  );
}

"use client";

import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { BrandLogo } from "./BrandLogo";

type Props = {
  href?: string;
  logoVariant?: "mark" | "icon";
  logoSize?: number;
  className?: string;
  priority?: boolean;
  loading?: "lazy" | "eager";
};

export function BrandLockup({
  href,
  logoVariant = "mark",
  logoSize,
  className = "",
  priority,
  loading = "lazy",
}: Props) {
  const iconSize = logoSize ?? (logoVariant === "mark" ? 44 : 52);
  const content = (
    <>
      <BrandLogo
        variant={logoVariant}
        width={iconSize}
        height={iconSize}
        priority={priority}
        loading={loading}
      />
      <span className="rtas-header__brand-text">
        <span className="rtas-header__wordmark">RTAS</span>
        <span className="rtas-header__product">Studio AI</span>
      </span>
    </>
  );

  if (href) {
    return (
      <Link
        href={href}
        className={`rtas-header__brand ${className}`.trim()}
        aria-label={`${PRODUCT_NAME} home`}
      >
        {content}
      </Link>
    );
  }

  return (
    <div className={`rtas-header__brand ${className}`.trim()} aria-label={PRODUCT_NAME}>
      {content}
    </div>
  );
}

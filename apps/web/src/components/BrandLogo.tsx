"use client";

import {
  BRAND_FAVICON_PATH,
  BRAND_LOGO_PATH,
} from "@/lib/brand-assets";

type Props = {
  /** mark = circular logo + text in headers; full = larger lockup; icon = R favicon mark */
  variant?: "mark" | "full" | "icon";
  width?: number;
  height?: number;
  className?: string;
};

export function BrandLogo({
  variant = "mark",
  width,
  height,
  className = "",
}: Props) {
  const src =
    variant === "icon" || variant === "mark"
      ? BRAND_FAVICON_PATH
      : BRAND_LOGO_PATH;
  const w = width ?? (variant === "full" ? 72 : variant === "icon" ? 32 : 44);
  const h = height ?? w;

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt="RTAS Studio AI"
      width={w}
      height={h}
      className={`brand-logo brand-logo--${variant} ${className}`.trim()}
    />
  );
}

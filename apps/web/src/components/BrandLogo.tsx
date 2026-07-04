"use client";

import Image from "next/image";
import {
  BRAND_FAVICON_PATH,
  BRAND_LOGO_PATH,
  BRAND_LOGO_SIZES,
} from "@/lib/brand-assets";

type Props = {
  /** mark = circular logo + text in headers; full = larger lockup; icon = R favicon mark */
  variant?: "mark" | "full" | "icon";
  width?: number;
  height?: number;
  className?: string;
  /** Above-the-fold header logos — improves LCP */
  priority?: boolean;
  loading?: "lazy" | "eager";
};

export function BrandLogo({
  variant = "mark",
  width,
  height,
  className = "",
  priority = false,
  loading,
}: Props) {
  const src =
    variant === "icon" || variant === "mark"
      ? BRAND_FAVICON_PATH
      : BRAND_LOGO_PATH;
  const defaults = BRAND_LOGO_SIZES[variant];
  const w = width ?? defaults.width;
  const h = height ?? defaults.height;

  return (
    <Image
      src={src}
      alt="RTAS Studio AI"
      width={w}
      height={h}
      className={`brand-logo brand-logo--${variant} ${className}`.trim()}
      priority={priority}
      loading={priority ? undefined : (loading ?? "lazy")}
    />
  );
}

export const fontFamily = {
  sans: 'var(--font-inter, "Inter"), system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
  mono: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
} as const;

export const fontSize = {
  xs: "0.75rem",
  sm: "0.875rem",
  base: "1rem",
  md: "0.95rem",
  lg: "1.125rem",
  xl: "1.25rem",
  "2xl": "1.5rem",
  "3xl": "1.875rem",
  "4xl": "2.25rem",
  "5xl": "3rem",
  "6xl": "3.75rem",
} as const;

export const lineHeight = {
  none: "1",
  tight: "1.25",
  snug: "1.375",
  normal: "1.5",
  relaxed: "1.625",
  loose: "2",
} as const;

export const fontWeight = {
  normal: "400",
  medium: "500",
  semibold: "600",
  bold: "700",
} as const;

export const letterSpacing = {
  tighter: "-0.05em",
  tight: "-0.02em",
  normal: "0",
  wide: "0.025em",
  wider: "0.05em",
  widest: "0.08em",
} as const;

/** Named typography presets for headings and body copy */
export const typographyPresets = {
  display: {
    fontSize: fontSize["5xl"],
    lineHeight: lineHeight.tight,
    fontWeight: fontWeight.bold,
    letterSpacing: letterSpacing.tight,
  },
  h1: {
    fontSize: fontSize["4xl"],
    lineHeight: lineHeight.tight,
    fontWeight: fontWeight.bold,
    letterSpacing: letterSpacing.tight,
  },
  h2: {
    fontSize: fontSize["3xl"],
    lineHeight: lineHeight.snug,
    fontWeight: fontWeight.semibold,
    letterSpacing: letterSpacing.tight,
  },
  h3: {
    fontSize: fontSize["2xl"],
    lineHeight: lineHeight.snug,
    fontWeight: fontWeight.semibold,
  },
  h4: {
    fontSize: fontSize.xl,
    lineHeight: lineHeight.normal,
    fontWeight: fontWeight.semibold,
  },
  body: {
    fontSize: fontSize.base,
    lineHeight: lineHeight.normal,
    fontWeight: fontWeight.normal,
  },
  bodySm: {
    fontSize: fontSize.sm,
    lineHeight: lineHeight.normal,
    fontWeight: fontWeight.normal,
  },
  caption: {
    fontSize: fontSize.xs,
    lineHeight: lineHeight.normal,
    fontWeight: fontWeight.medium,
    letterSpacing: letterSpacing.widest,
  },
  eyebrow: {
    fontSize: fontSize.xs,
    lineHeight: lineHeight.normal,
    fontWeight: fontWeight.semibold,
    letterSpacing: letterSpacing.widest,
  },
} as const;

export type FontFamily = typeof fontFamily;
export type FontSize = typeof fontSize;
export type TypographyPreset = typeof typographyPresets;

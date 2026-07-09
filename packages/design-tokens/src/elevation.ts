export const elevation = {
  none: "none",
  sm: "0 1px 2px rgba(0, 0, 0, 0.35)",
  md: "0 4px 12px rgba(0, 0, 0, 0.35)",
  lg: "0 12px 32px rgba(0, 0, 0, 0.4)",
  xl: "0 20px 48px rgba(0, 0, 0, 0.45)",
  "2xl": "0 24px 48px rgba(0, 0, 0, 0.45)",
  header: "0 8px 32px rgba(0, 0, 0, 0.5)",
  panel: "0 12px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.04)",
  cardHover:
    "0 0 24px rgba(168, 85, 247, 0.18), 0 20px 48px rgba(0, 0, 0, 0.45)",
  cardHoverGold: "0 0 20px rgba(180, 83, 9, 0.2)",
  widgetHover:
    "0 0 18px rgba(168, 85, 247, 0.12), 0 16px 40px rgba(0, 0, 0, 0.42)",
  glowPurple: "0 0 24px rgba(168, 85, 247, 0.18)",
  glowPurpleHeader: "0 0 24px rgba(88, 28, 135, 0.15)",
  glowGold: "0 0 20px rgba(180, 83, 9, 0.2)",
  textGlowPurple: "0 0 10px rgba(168, 85, 247, 0.35)",
} as const;

export const backdropBlur = {
  sm: "4px",
  md: "8px",
  lg: "10px",
  xl: "12px",
  "2xl": "14px",
} as const;

export type Elevation = typeof elevation;
export type BackdropBlur = typeof backdropBlur;

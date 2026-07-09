export const duration = {
  instant: "0ms",
  fast: "150ms",
  normal: "280ms",
  slow: "400ms",
  slower: "600ms",
} as const;

export const easing = {
  linear: "linear",
  default: "cubic-bezier(0.4, 0, 0.2, 1)",
  in: "cubic-bezier(0.4, 0, 1, 1)",
  out: "cubic-bezier(0, 0, 0.2, 1)",
  inOut: "cubic-bezier(0.4, 0, 0.2, 1)",
  bounce: "cubic-bezier(0.34, 1.56, 0.64, 1)",
  spring: "cubic-bezier(0.22, 1, 0.36, 1)",
} as const;

/** Composite transition shorthands */
export const transition = {
  none: "none",
  fast: `${duration.fast} ${easing.default}`,
  smooth: `${duration.normal} ${easing.default}`,
  slow: `${duration.slow} ${easing.default}`,
  spring: `${duration.slow} ${easing.spring}`,
} as const;

/** Named motion presets for components and pages */
export const motionPresets = {
  fadeIn: {
    duration: duration.normal,
    easing: easing.out,
    keyframes: "rtas-fade-in",
  },
  fadeOut: {
    duration: duration.fast,
    easing: easing.in,
    keyframes: "rtas-fade-out",
  },
  slideUp: {
    duration: duration.normal,
    easing: easing.spring,
    keyframes: "rtas-slide-up",
  },
  slideDown: {
    duration: duration.normal,
    easing: easing.spring,
    keyframes: "rtas-slide-down",
  },
  scaleIn: {
    duration: duration.normal,
    easing: easing.bounce,
    keyframes: "rtas-scale-in",
  },
  shimmer: {
    duration: duration.slower,
    easing: easing.linear,
    keyframes: "rtas-shimmer",
  },
  pulse: {
    duration: "2s",
    easing: easing.inOut,
    keyframes: "rtas-pulse",
  },
  meshDrift: {
    duration: "18s",
    easing: easing.linear,
    keyframes: "rtas-mesh-drift",
  },
} as const;

export type Duration = typeof duration;
export type Easing = typeof easing;
export type Transition = typeof transition;
export type MotionPreset = typeof motionPresets;

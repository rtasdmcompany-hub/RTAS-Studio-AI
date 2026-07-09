import { colorPrimitives, colorSemantic } from "./colors";
import {
  fontFamily,
  fontSize,
  fontWeight,
  letterSpacing,
  lineHeight,
  typographyPresets,
} from "./typography";
import { spacing } from "./spacing";
import { radius } from "./radius";
import { backdropBlur, elevation } from "./elevation";
import { duration, easing, motionPresets, transition } from "./motion";

export {
  colorPrimitives,
  colorSemantic,
  type ColorPrimitive,
  type ColorSemantic,
} from "./colors";
export {
  fontFamily,
  fontSize,
  fontWeight,
  letterSpacing,
  lineHeight,
  typographyPresets,
  type FontFamily,
  type FontSize,
  type TypographyPreset,
} from "./typography";
export { spacing, type Spacing } from "./spacing";
export { radius, type Radius } from "./radius";
export {
  backdropBlur,
  elevation,
  type BackdropBlur,
  type Elevation,
} from "./elevation";
export {
  duration,
  easing,
  motionPresets,
  transition,
  type Duration,
  type Easing,
  type MotionPreset,
  type Transition,
} from "./motion";

/** Flat token map for programmatic theming */
export const designTokens = {
  color: {
    primitive: colorPrimitives,
    semantic: colorSemantic,
  },
  typography: {
    fontFamily,
    fontSize,
    fontWeight,
    letterSpacing,
    lineHeight,
    presets: typographyPresets,
  },
  spacing,
  radius,
  elevation,
  backdropBlur,
  motion: {
    duration,
    easing,
    transition,
    presets: motionPresets,
  },
} as const;

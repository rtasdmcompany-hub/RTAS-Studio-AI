/**
 * Landing conversion copy — keep brand-first, calm, international.
 * Prices always come from @rtas/shared constants.
 */

export const LANDING_BRAND = "RTAS STUDIO AI";

export const LANDING_HERO_HEADLINE =
  "Cinematic AI videos with identity lock — from beat to publish.";

export const LANDING_HERO_SUPPORT =
  "The international studio for music videos, ads, and stories. Compose once, render with face consistency, publish with commercial-ready exports.";

export const LANDING_AUDIENCES = [
  {
    id: "artists",
    title: "Artists & rappers",
    body: "Sync lyrics and audio into identity-locked performance videos.",
  },
  {
    id: "brands",
    title: "Brands & agencies",
    body: "Ship scroll-stopping ads without a multi-tool production stack.",
  },
  {
    id: "studios",
    title: "Creators & studios",
    body: "One workspace for compose, render, library, and share.",
  },
] as const;

export const LANDING_OUTCOMES = [
  {
    id: "credits",
    label: "1 credit = 1 second",
    detail: "Transparent render economics — no opaque token math.",
  },
  {
    id: "identity",
    label: "Identity lock",
    detail: "Real-face mode keeps likeness consistent shot after shot.",
  },
  {
    id: "pipeline",
    label: "Compose → Render → Publish",
    detail: "One guided studio. No handoffs. No starting over.",
  },
] as const;

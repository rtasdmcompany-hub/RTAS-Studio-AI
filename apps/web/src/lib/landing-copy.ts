/**
 * Landing conversion copy — keep brand-first, calm, international.
 * Prices always come from @rtas/shared constants.
 */

export const LANDING_BRAND = "RTAS STUDIO AI";

export const LANDING_HERO_HEADLINE =
  "Cinematic AI videos with Authorized Identity Preservation — from beat to publish.";

export const LANDING_HERO_SUPPORT =
  "The international AI video studio for music videos, ads, and stories. Compose once, render with authorized identity consistency on content you own, publish with commercial-ready exports.";

export const LANDING_AUDIENCES = [
  {
    id: "artists",
    title: "Artists & rappers",
    body: "Sync lyrics and audio into identity-consistent performance videos.",
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
    label: "Authorized Identity Preservation",
    detail: "Keeps a likeness you own or are authorized to use consistent shot after shot — not face-swap marketing.",
  },
  {
    id: "pipeline",
    label: "Compose → Render → Publish",
    detail: "One guided studio. No handoffs. No starting over.",
  },
] as const;

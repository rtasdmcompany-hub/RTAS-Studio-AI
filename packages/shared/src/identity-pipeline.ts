/** Backend placeholders: IP-Adapter / InstantID / provider face-lock */
export type IdentityProvider =
  | "instant-id"
  | "ip-adapter"
  | "kling-character-id";

export interface IdentityPipelineConfig {
  enabled: boolean;
  provider: IdentityProvider;
  /** 0–1 — maps to IP-Adapter / InstantID strength when wired */
  identityStrength: number;
  ipAdapterEnabled: boolean;
  instantIdEnabled: boolean;
  /** Reference asset key from form file upload */
  faceReferenceFieldId: string;
  preserveGenuineFace: boolean;
}

export function defaultIdentityPipeline(
  enabled = false
): IdentityPipelineConfig {
  return {
    enabled,
    provider: "instant-id",
    identityStrength: 0.85,
    ipAdapterEnabled: true,
    instantIdEnabled: true,
    faceReferenceFieldId: "faceReference",
    preserveGenuineFace: true,
  };
}

export function identityPipelineForVisualStyle(
  visualStyle: "real" | "avatar" | "cartoon"
): IdentityPipelineConfig {
  if (visualStyle !== "real") {
    return defaultIdentityPipeline(false);
  }
  return {
    ...defaultIdentityPipeline(true),
    provider: "instant-id",
    ipAdapterEnabled: true,
    instantIdEnabled: true,
    preserveGenuineFace: true,
  };
}

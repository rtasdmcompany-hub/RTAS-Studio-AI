export type IdentityProvider =
  | "instant-id"
  | "ip-adapter"
  | "kling-character-id";

export interface IdentityPipelineConfig {
  enabled: boolean;
  provider: IdentityProvider;
  identityStrength: number;
  ipAdapterEnabled: boolean;
  instantIdEnabled: boolean;
  faceReferenceFieldId: string;
  preserveGenuineFace: boolean;
}

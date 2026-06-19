import type { GenerationRequest, IdentityPipelineConfig, VisualStyle } from "@rtas/shared";

export type GenerateBody = GenerationRequest & {
  identityPipeline?: IdentityPipelineConfig;
  files?: Record<string, { name: string; mimeType: string; size: number }>;
};

/** Builds provider-ready prompt from category fields */
export function buildProviderPrompt(req: GenerateBody): string {
  const parts: string[] = [
    `Category: ${req.category}`,
    `Visual style: ${req.visualStyle}`,
    `Duration: ${req.durationSeconds}s`,
  ];

  if (req.mode === "prompt" && req.fields.mainPrompt) {
    parts.push(req.fields.mainPrompt);
  }

  Object.entries(req.fields).forEach(([key, value]) => {
    if (!value || key === "mainPrompt" || key === "faceConsent") return;
    if (key === "duration") return;
    parts.push(`${key}: ${value}`);
  });

  if (req.files && Object.keys(req.files).length > 0) {
    parts.push(
      `Attachments: ${Object.entries(req.files)
        .map(([k, v]) => `${k}=${v.name}`)
        .join(", ")}`
    );
  }

  if (req.identityPipeline?.enabled) {
    parts.push(
      `Identity pipeline: ${req.identityPipeline.provider}, strength=${req.identityPipeline.identityStrength}, ipAdapter=${req.identityPipeline.ipAdapterEnabled}, instantId=${req.identityPipeline.instantIdEnabled}`
    );
  }

  if (req.visualStyle === "real") {
    parts.push(
      "CRITICAL: Preserve exact facial identity from reference. No face alteration, morphing, or replacement. Photorealistic, genuine likeness."
    );
  } else if (req.visualStyle === "avatar") {
    parts.push("Professional AI avatar presenter, consistent identity.");
  } else {
    parts.push("Animated cartoon style, child-safe, vibrant colors.");
  }

  return parts.join("\n");
}

export function providerForStyle(
  style: VisualStyle,
  pipeline?: IdentityPipelineConfig
): string {
  if (style === "real" && pipeline?.instantIdEnabled) {
    return "instant-id";
  }
  if (style === "real" && pipeline?.ipAdapterEnabled) {
    return "ip-adapter";
  }
  switch (style) {
    case "real":
      return "kling-character-id";
    case "avatar":
      return "runway-gen4";
    case "cartoon":
      return "fal-cartoon";
    default:
      return "replicate-default";
  }
}

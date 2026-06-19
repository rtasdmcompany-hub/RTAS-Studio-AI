import { NextResponse } from "next/server";
import { creditsForDuration, FREE_TRIAL_DURATION_SECONDS } from "@rtas/shared";
import { buildProviderPrompt, providerForStyle, type GenerateBody } from "@/lib/generation";

/** Request lock — only one demo generation at a time (mirrors FastAPI /api/generate guard). */
let generationInProgress = false;

/**
 * Demo Next.js handler. Live Fal.ai calls run through FastAPI (apps/backend).
 * Production studio uses postGenerateToBackend → localhost:8000/api/generate.
 */
export async function POST(request: Request) {
  if (generationInProgress) {
    console.error("Generation conflict: a generation is already in progress.");
    return NextResponse.json(
      { error: "A video generation is already in progress. Please wait for it to finish." },
      { status: 409 }
    );
  }

  generationInProgress = true;

  try {
    const body = await request.json();
    const {
      mode,
      category,
      visualStyle,
      durationSeconds,
      fields,
      files,
      identityPipeline,
      profile,
      previewOnly,
      useFreeTrial,
    } = body as GenerateBody & {
      profile?: { subscriptionActive?: boolean; credits?: number };
      previewOnly?: boolean;
      useFreeTrial?: boolean;
    };

    if (!mode || !category || !visualStyle || !durationSeconds) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    if (visualStyle === "real") {
      const consent = fields?.faceConsent?.trim().toUpperCase();
      const hasFaceFile = Boolean(files?.faceReference);
      if (!hasFaceFile || consent !== "YES") {
        return NextResponse.json(
          { error: "Real face mode requires Face Photo upload and consent (YES)" },
          { status: 400 }
        );
      }
    }

    const req: GenerateBody = {
      mode,
      category,
      visualStyle,
      durationSeconds,
      fields: fields ?? {},
      files,
      identityPipeline,
    };

    const prompt = buildProviderPrompt(req);
    const provider = providerForStyle(visualStyle, identityPipeline);
    const creditsUsed = useFreeTrial ? 0 : creditsForDuration(durationSeconds);

    const demoVideoUrl =
      "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4";

    return NextResponse.json({
      ok: true,
      jobId: `job_${Date.now()}`,
      provider,
      identityPipeline: identityPipeline ?? null,
      promptPreview: prompt.slice(0, 200),
      creditsUsed,
      previewOnly: !!previewOnly,
      canDownload:
        !previewOnly &&
        !!profile?.subscriptionActive &&
        (profile?.credits ?? 0) > 0,
      videoUrl: demoVideoUrl,
      durationSeconds: useFreeTrial
        ? Math.min(durationSeconds, FREE_TRIAL_DURATION_SECONDS)
        : durationSeconds,
      message:
        process.env.RUNWAY_API_KEY || process.env.KLING_API_KEY
          ? "Queued for AI provider"
          : "Demo mode: add API keys in .env.local for real generation",
    });
  } catch (e) {
    const message = e instanceof Error ? e.message : "Generation failed";
    console.error("Fal API Error:", message);
    return NextResponse.json({ error: message }, { status: 500 });
  } finally {
    generationInProgress = false;
  }
}

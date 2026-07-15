import type { VideoCategory } from "@rtas/shared";

export type HowToCategoryGuide = {
  id: VideoCategory;
  title: string;
  media: { type: "video" | "image"; src: string; alt: string };
  summary: string;
  valueTags: string[];
  bestFor: string[];
  recommended: {
    mode: string;
    visualStyle: string;
    length: string;
  };
  steps: { title: string; detail: string }[];
  tips: string[];
};

export const UNIVERSAL_STEPS = [
  {
    num: "01",
    tag: "Secure access",
    tagVariant: "purple" as const,
    title: "Step 1: Authenticate & Initialize Studio",
    detail:
      "Create your workspace with Secure OAuth (Google) or verified email credentials. Once authenticated, launch Studio from the header to initialize your session, sync credits, and unlock the full cinematic pipeline.",
  },
  {
    num: "02",
    tag: "Pipeline setup",
    tagVariant: "gold" as const,
    title: "Step 2: Configure Your Production Pipeline",
    detail:
      "Select Prompt or Image mode, choose your video category, set Real / Avatar / Cartoon visual style, and name your project. Each choice calibrates the Audio-Driven Cinematic Engine for your deliverable.",
  },
  {
    num: "03",
    tag: "Guided wizard",
    tagVariant: "purple" as const,
    title: "Step 3: Complete the Guided Creation Wizard",
    detail:
      "Category-specific fields appear progressively — lyrics, scripts, character sheets, and direction prompts. Required inputs must validate before the wizard advances to render configuration.",
  },
  {
    num: "04",
    tag: "Render & QA",
    tagVariant: "gold" as const,
    title: "Step 4: Launch Render & Quality Preview",
    detail:
      "Trigger Generate video to start GPU-backed rendering with live progress telemetry. Review the full master on the Preview screen before export — verify motion, identity lock, and lyric sync.",
  },
  {
    num: "05",
    tag: "Commercial export",
    tagVariant: "purple" as const,
    title: "Step 5: Export with Commercial License",
    detail:
      "Free trial delivers a watermarked evaluation render. Upgrade to Tester, Standard, or Premium for clean commercial downloads, full HD/4K output, and licensed distribution rights.",
  },
] as const;

export const STUDIO_FLOW = [
  {
    label: "Input mode",
    options: "Prompt (text-to-video) · Image (photo-to-video reference lock)",
  },
  {
    label: "Content category",
    options: "Song · Religious · Business · Cartoon · Story · Podcast",
  },
  {
    label: "Visual identity",
    options:
      "Real — 100% Consistent Real-Face Mode · Avatar · Cartoon stylization",
  },
  {
    label: "Wizard & render",
    options: "Project metadata, duration, category fields, Generate",
  },
] as const;

export const CATEGORY_GUIDES: HowToCategoryGuide[] = [
  {
    id: "song",
    title: "Song / Rap / Music Video",
    media: { type: "video", src: "/showcase/rap.mp4", alt: "Rap music video example" },
    summary:
      "Deploy the Audio-Driven Cinematic Engine for rap, pop, and performance clips — with Lyric-Synced Motion Timelines and optional master audio upload for broadcast-grade timing.",
    valueTags: [
      "Audio-Driven Cinematic Engine",
      "Lyric-Synced Motion Timelines",
      "100% Consistent Real-Face Mode",
    ],
    bestFor: [
      "Rap and hip-hop performance clips",
      "Pop and acoustic release promos",
      "Lyric videos for YouTube, Reels, and TikTok",
    ],
    recommended: {
      mode: "Prompt mode — paste lyrics and music-style direction",
      visualStyle:
        "Real or Avatar for performers; enable Identity Shielding for on-camera artists",
      length: "15–60 seconds for social; up to 3 minutes for full-song segments",
    },
    steps: [
      {
        title: "Initialize Song category",
        detail: "Studio setup → Category → Music to activate lyric-sync pipelines.",
      },
      {
        title: "Load Lyric-Synced Motion Timelines",
        detail: "Paste full lyrics in the Lyrics field, including chorus and bridge markers.",
      },
      {
        title: "Calibrate music style",
        detail: "Define genre tags: trap, drill, acoustic, soft pop — drives scene pacing.",
      },
      {
        title: "Attach audio reference (optional)",
        detail: "Upload MP3/WAV to anchor the Audio-Driven Cinematic Engine to your master.",
      },
      {
        title: "Direct cinematic motion",
        detail: "Specify camera paths, mood, neon concert energy, slow motion, and cut rhythm.",
      },
    ],
    tips: [
      "Enable Real style with Identity Shielding and a front-facing photo for performer lock.",
      "Keep first renders under 30 seconds to optimize credit consumption during testing.",
    ],
  },
  {
    id: "religious",
    title: "Islamic / Faith",
    media: {
      type: "video",
      src: "/showcase/islamic.mp4",
      alt: "Respectful mosque and faith-based video example",
    },
    summary:
      "Produce respectful mosque and faith content with tone-controlled direction prompts and optional Real-Face Mode for speakers and community leaders.",
    valueTags: ["Tone-Controlled Direction", "Real-Face Mode", "Faith Scripts"],
    bestFor: [
      "Prayer and worship visuals",
      "Holiday and festival campaigns",
      "Short faith reminders and parables",
    ],
    recommended: {
      mode: "Prompt mode with structured script or sacred reading",
      visualStyle: "Real or Avatar for speakers; calm Cartoon for youth audiences",
      length: "15–60 seconds for social distribution",
    },
    steps: [
      { title: "Select Faith category", detail: "Category → Islamic / Faith." },
      {
        title: "Define thematic focus",
        detail: "Examples: gratitude, forgiveness, holiday, daily reflection, parable.",
      },
      {
        title: "Input script or reading",
        detail: "Sacred text, prayer, hymn lyrics, or narration aligned to your tradition.",
      },
      { title: "Set emotional tone", detail: "Calm, uplifting, educational, or celebratory." },
      {
        title: "Apply respectful direction",
        detail: "Soft light, dignified visuals, minimal intrusive overlays.",
      },
    ],
    tips: [
      "Use wording that is accurate and respectful for your faith community.",
      "30-second calm-tone clips perform strongly on social status formats.",
    ],
  },
  {
    id: "cartoon",
    title: "Kids",
    media: { type: "video", src: "/showcase/cartoon.mp4", alt: "Kids animation example" },
    summary:
      "Launch stylized animation pipelines for age-appropriate storytelling with character-locked prompts and family-safe visual defaults.",
    valueTags: ["Stylized Animation Pipeline", "Character Lock Prompts", "Age-Safe Defaults"],
    bestFor: ["Kids moral stories", "Edutainment clips", "Serialized episode shorts"],
    recommended: {
      mode: "Prompt mode with structured narrative",
      visualStyle: "Cartoon (required for animated output)",
      length: "15–60 seconds per episode segment",
    },
    steps: [
      { title: "Select Kids category", detail: "Category → Kids." },
      { title: "Define character roster", detail: "Name each character and describe visual traits." },
      { title: "Outline story arc", detail: "Beginning, conflict, and resolution in clear beats." },
      { title: "Set audience age band", detail: "Examples: ages 3–6 or 7–10 for tone calibration." },
      {
        title: "Upload style reference",
        detail: "Optional drawing or screenshot to match palette and line weight.",
      },
    ],
    tips: [
      "Confirm Visual style → Cartoon before initiating render.",
      "Use short sentences in the story field for clearer scene segmentation.",
    ],
  },
  {
    id: "podcast",
    title: "Podcast Clip",
    media: { type: "video", src: "/showcase/solo.mp4", alt: "Podcast talking-head example" },
    summary:
      "Convert long-form audio into studio-grade talking-head clips with 100% Consistent Real-Face Mode and Identity Shielding for host recognition across episodes.",
    valueTags: [
      "Real-Face Mode",
      "Identity Shielding",
      "Talking-Head Studio Pipeline",
    ],
    bestFor: [
      "YouTube Shorts from podcast archives",
      "Episode launch teasers",
      "Quote clips for social distribution",
    ],
    recommended: {
      mode: "Prompt mode with structured talking points",
      visualStyle: "Real (face lock) or Avatar spokesperson",
      length: "15–60 second highlight clip",
    },
    steps: [
      { title: "Select Podcast category", detail: "Category → Podcast." },
      { title: "Register host identity", detail: "Display name for on-screen attribution." },
      { title: "Set episode title", detail: "Short headline for this clip or series entry." },
      {
        title: "Load talking points",
        detail: "Three to five key topics the host covers in this segment.",
      },
      { title: "Configure set design", detail: "Studio desk, dark room, or minimal branded backdrop." },
    ],
    tips: [
      "Real style requires a clear front-face photo and YES consent for Identity Shielding.",
      "Upload cover art for branded lower-thirds and episode continuity.",
    ],
  },
  {
    id: "business",
    title: "Business / Commercial Ad",
    media: { type: "video", src: "/showcase/commercial.mp4", alt: "Commercial ad example" },
    summary:
      "Ship conversion-focused ad creatives with product-accurate Image mode references and CTA-optimized script structures for global campaigns.",
    valueTags: ["Product-Accurate Image Mode", "CTA Script Engine", "Commercial License Ready"],
    bestFor: ["Product launches", "Performance marketing ads", "Brand Reels and paid social"],
    recommended: {
      mode: "Prompt or Image mode with product photography",
      visualStyle: "Real or Avatar spokesperson; Image mode for SKU-accurate shots",
      length: "15–30 seconds for ads; up to 1 minute for explainers",
    },
    steps: [
      { title: "Select Business category", detail: "Category → Business Ad." },
      { title: "Register brand entity", detail: "Company or product name for on-screen identity." },
      { title: "Define offer & CTA", detail: "Example: 50% off — order today at yourstore.com." },
      { title: "Author ad script", detail: "Unified voiceover and on-screen copy in one field." },
      { title: "Upload product asset", detail: "Reference photo for accurate product visualization." },
    ],
    tips: [
      "Image mode excels when SKU photography already exists in your asset library.",
      "Place the primary CTA in the final three seconds of the script.",
    ],
  },
  {
    id: "story",
    title: "Story / Short Film",
    media: { type: "video", src: "/showcase/solo.mp4", alt: "Cinematic story example" },
    summary:
      "Direct narrative micro-films with plot-driven prompts, cinematic direction controls, and optional Real-Face Mode for character continuity across scenes.",
    valueTags: [
      "Cinematic Direction Controls",
      "Plot-Driven Segmentation",
      "Real-Face Mode",
    ],
    bestFor: ["Micro-drama", "Comedy skits", "Thriller and teaser trailers"],
    recommended: {
      mode: "Prompt mode with structured three-act plot",
      visualStyle: "Real, Avatar, or Cartoon depending on genre",
      length: "30 seconds to 3 minutes depending on plan tier",
    },
    steps: [
      { title: "Select Story category", detail: "Category → Story." },
      { title: "Set genre", detail: "Drama, comedy, romance, thriller, and more." },
      { title: "Outline plot structure", detail: "Beginning, conflict, and resolution in distinct paragraphs." },
      { title: "Upload scene reference", detail: "Optional still for location look and color grade." },
      {
        title: "Apply cinematic direction",
        detail: "Camera movement, lighting, pacing — golden hour, handheld, anamorphic.",
      },
    ],
    tips: [
      "Segment long plots into 15-second beats for clearer scene generation.",
      "Use direction prompts to enforce a consistent film look across cuts.",
    ],
  },
];

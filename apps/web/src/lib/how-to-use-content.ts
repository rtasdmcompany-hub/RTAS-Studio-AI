import type { VideoCategory } from "@rtas/shared";

export type HowToCategoryGuide = {
  id: VideoCategory;
  title: string;
  media: { type: "video" | "image"; src: string; alt: string };
  summary: string;
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
    num: "1",
    title: "Sign in and open Studio",
    detail: "Create a free account or sign in with Google, then open Studio from the header.",
  },
  {
    num: "2",
    title: "Choose mode, category, style, and title",
    detail: "Select Prompt or Image mode, your video category, Real / Avatar / Cartoon style, and a project title.",
  },
  {
    num: "3",
    title: "Complete the wizard",
    detail: "Each category shows different fields — lyrics, script, characters, and more. Required fields must be filled before Next is enabled.",
  },
  {
    num: "4",
    title: "Generate and preview",
    detail: "Click Generate video, watch the progress bar, then review the full video on the Preview screen.",
  },
  {
    num: "5",
    title: "Download with Premium",
    detail: "Free trial shows a watermarked preview. Upgrade for a clean commercial download.",
  },
] as const;

export const STUDIO_FLOW = [
  { label: "Mode", options: "Prompt (text to video) · Image (photo to video)" },
  {
    label: "Category",
    options: "Song · Islamic · Business · Cartoon · Story · Podcast",
  },
  {
    label: "Visual style",
    options: "Real (face lock) · Avatar · Cartoon",
  },
  { label: "Title and wizard", options: "Project name, length, fields, Generate" },
] as const;

export const CATEGORY_GUIDES: HowToCategoryGuide[] = [
  {
    id: "song",
    title: "Song / Rap / Music Video",
    media: { type: "video", src: "/showcase/rap.mp4", alt: "Rap music video example" },
    summary: "Lyric-synced music videos for rap, pop, and performance clips with optional audio upload.",
    bestFor: ["Rap and hip-hop clips", "Pop and acoustic songs", "Lyric videos for YouTube and Reels"],
    recommended: {
      mode: "Prompt mode — paste lyrics and music style",
      visualStyle: "Real or Avatar for performers; Cartoon for animated lyric videos",
      length: "15–60 seconds for social; up to 3 minutes for full song clips",
    },
    steps: [
      { title: "Select Song category", detail: "Studio setup → Category → Song Video." },
      { title: "Paste lyrics", detail: "Add full lyrics in the Lyrics box, including chorus lines." },
      { title: "Music style", detail: "Examples: trap, acoustic, drill, soft pop." },
      {
        title: "Optional audio and image",
        detail: "Upload MP3/WAV for timing; add a reference image for cover art look.",
      },
      {
        title: "Direction prompt",
        detail: "Describe camera moves, mood, city lights, slow motion, and pacing.",
      },
    ],
    tips: [
      "Use Real style with a clear face photo if the singer must look like you.",
      "Keep first test videos under 30 seconds to save credits.",
    ],
  },
  {
    id: "islamic",
    title: "Islamic Video",
    media: { type: "video", src: "/showcase/islamic.mp4", alt: "Islamic nasheed video example" },
    summary: "Nasheeds, daily reminders, Ramadan content, and respectful faith-based visuals.",
    bestFor: ["Nasheed visuals", "Short reminders", "Ramadan and Jummah posts"],
    recommended: {
      mode: "Prompt mode with a clear script",
      visualStyle: "Real or Avatar for speakers; calm Cartoon for children",
      length: "15–60 seconds for social status clips",
    },
    steps: [
      { title: "Select Islamic category", detail: "Category → Islamic Video." },
      { title: "Topic", detail: "Examples: patience, Ramadan, gratitude, daily reminder." },
      { title: "Script or verses", detail: "Arabic text, translation, or narration script." },
      { title: "Tone", detail: "Calm, inspiring, or educational." },
      { title: "Direction", detail: "Soft light, respectful B-roll, minimal text overlays." },
    ],
    tips: [
      "Double-check spelling and wording for accuracy and respect.",
      "Calm tone with 30-second length works well for status videos.",
    ],
  },
  {
    id: "cartoon",
    title: "Kids Cartoon",
    media: { type: "video", src: "/showcase/cartoon.mp4", alt: "Kids cartoon animation example" },
    summary: "Animated stories for children with simple characters and age-friendly plots.",
    bestFor: ["Kids moral stories", "Learning clips", "Fun episode shorts"],
    recommended: {
      mode: "Prompt mode",
      visualStyle: "Cartoon (required)",
      length: "15–60 seconds per episode clip",
    },
    steps: [
      { title: "Select Cartoon category", detail: "Category → Kids Cartoon." },
      { title: "Characters", detail: "Name each character and describe their look." },
      { title: "Story", detail: "Describe beginning, problem, and happy ending." },
      { title: "Age group", detail: "Examples: ages 3–6 or 7–10." },
      {
        title: "Style reference",
        detail: "Upload a drawing or screenshot to match colors and style.",
      },
    ],
    tips: [
      "Select Visual style → Cartoon before generating.",
      "Use short sentences in the story box for clearer animation.",
    ],
  },
  {
    id: "podcast",
    title: "Podcast Clip",
    media: { type: "video", src: "/showcase/solo.mp4", alt: "Podcast talking-head example" },
    summary: "Talking-head clips from your podcast with a studio-style background.",
    bestFor: ["YouTube Shorts from podcasts", "Episode teasers", "Quote clips for social"],
    recommended: {
      mode: "Prompt mode",
      visualStyle: "Real (face lock) or Avatar",
      length: "15–60 second highlight clip",
    },
    steps: [
      { title: "Select Podcast category", detail: "Category → Podcast." },
      { title: "Host name", detail: "Name shown on screen or in the intro." },
      { title: "Episode title", detail: "Short title for this clip." },
      { title: "Talking points", detail: "Three to five key topics for the host to cover." },
      { title: "Background", detail: "Studio, dark room, or minimal desk setup." },
    ],
    tips: [
      "Real style requires a clear front face photo and typing YES for consent.",
      "Upload cover art for a branded lower-thirds look.",
    ],
  },
  {
    id: "business",
    title: "Business / Commercial Ad",
    media: { type: "video", src: "/showcase/commercial.mp4", alt: "Commercial ad example" },
    summary: "Product promos, brand ads, and call-to-action videos for business.",
    bestFor: ["Product launches", "Sale announcements", "Brand Reels"],
    recommended: {
      mode: "Prompt or Image mode with a product photo",
      visualStyle: "Real or Avatar spokesperson; Image mode for product shots",
      length: "15–30 seconds for ads; up to 1 minute for explainers",
    },
    steps: [
      { title: "Select Business category", detail: "Category → Business Ad." },
      { title: "Brand name", detail: "Your company or product name." },
      { title: "Offer or CTA", detail: "Example: 50% off — order today." },
      { title: "Ad script", detail: "Voiceover and on-screen text in one box." },
      { title: "Product image", detail: "Upload a product photo for accurate visuals." },
    ],
    tips: [
      "Image mode works well when you already have a product photo.",
      "Place your call to action in the last three seconds of the script.",
    ],
  },
  {
    id: "story",
    title: "Story / Short Film",
    media: { type: "video", src: "/showcase/solo.mp4", alt: "Cinematic story example" },
    summary: "Narrative shorts — drama, comedy, and thriller with plot-driven prompts.",
    bestFor: ["Micro-drama", "Comedy skits", "Thriller teasers"],
    recommended: {
      mode: "Prompt mode",
      visualStyle: "Real, Avatar, or Cartoon depending on genre",
      length: "30 seconds to 3 minutes depending on your plan",
    },
    steps: [
      { title: "Select Story category", detail: "Category → Story." },
      { title: "Genre", detail: "Drama, comedy, romance, thriller, and more." },
      { title: "Plot", detail: "Beginning, conflict, and ending in clear paragraphs." },
      { title: "Scene image", detail: "Optional reference still for look and location." },
      { title: "Direction prompt", detail: "Cinematic camera, lighting, and pacing notes." },
    ],
    tips: [
      "Break long plots into short scenes for clearer 15-second segments.",
      "Use the direction prompt for film look — golden hour, handheld, and so on.",
    ],
  },
];

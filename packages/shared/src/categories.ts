import type { CategoryField, VideoCategory } from "./types";

export const CATEGORY_META: Record<
  VideoCategory,
  { label: string; shortLabel: string; description: string }
> = {
  song: {
    label: "Music",
    shortLabel: "Music",
    description: "Singer performances and music videos with lyrics, style, and sync",
  },
  religious: {
    label: "Islamic / Faith",
    shortLabel: "Faith",
    description: "Respectful mosque and faith content — prayers, nasheeds, and teachings",
  },
  business: {
    label: "Business",
    shortLabel: "Business",
    description: "Commercial ads, product promos, and brand spots",
  },
  cartoon: {
    label: "Kids",
    shortLabel: "Kids",
    description: "Family-safe animation and kids storytelling",
  },
  story: {
    label: "Story",
    shortLabel: "Story",
    description: "Cinematic narratives and short-form films",
  },
  podcast: {
    label: "Podcast",
    shortLabel: "Podcast",
    description: "Talking-head clips, episode promos, and show highlights",
  },
};

export const DURATION_FIELD: CategoryField = {
  id: "duration",
  label: "Video Length",
  shortLabel: "Length",
  type: "select",
  required: true,
  options: [
    { value: "5", label: "5 sec" },
    { value: "15", label: "15 sec" },
    { value: "30", label: "30 sec" },
    { value: "60", label: "1 min" },
    { value: "180", label: "3 min" },
    { value: "300", label: "5 min" },
    { value: "600", label: "10 min" },
  ],
  helpText:
    "5 sec to 10 min — 1 credit = 1 second. Over 15 sec, RTAS renders in 15s parts and stitches one full video (Standard/Premium). Tester: max 30s.",
};

const directionPrompt: CategoryField = {
  id: "directionPrompt",
  label: "Directional Prompt",
  shortLabel: "Directional prompt",
  type: "textarea",
  placeholder: "Camera moves, mood, pacing, transitions…",
  required: false,
  helpText: "How the video should look and feel — camera, mood, pacing.",
};

/** Category-only fields (length shown separately in UI) */
export const CATEGORY_FIELDS: Record<VideoCategory, CategoryField[]> = {
  song: [
    {
      id: "lyrics",
      label: "Lyrics",
      shortLabel: "Lyrics",
      type: "textarea",
      required: true,
      placeholder: "Paste or write song lyrics…",
    },
    {
      id: "musicStyle",
      label: "Music Style",
      shortLabel: "Style",
      type: "text",
      required: true,
      placeholder: "e.g. acoustic pop, drill, nasheed",
    },
    {
      id: "audioSource",
      label: "Audio Source",
      shortLabel: "Audio",
      type: "file",
      accept: "audio/*",
      required: false,
      helpText: "MP3, WAV, or M4A track",
    },
    {
      id: "referenceImage",
      label: "Reference Image",
      shortLabel: "Image",
      type: "file",
      accept: "image/*",
      required: false,
      helpText: "Cover art or visual reference",
    },
    directionPrompt,
  ],
  religious: [
    {
      id: "topic",
      label: "Topic",
      shortLabel: "Topic",
      type: "text",
      required: true,
      placeholder: "e.g. gratitude, holiday, daily reflection, parable",
    },
    {
      id: "script",
      label: "Script / Reading",
      shortLabel: "Script",
      type: "textarea",
      required: true,
      placeholder: "Sacred text, prayer, hymn lyrics, or narration for your faith",
    },
    {
      id: "tone",
      label: "Tone",
      shortLabel: "Tone",
      type: "text",
      placeholder: "Calm, uplifting, educational, celebratory",
    },
    {
      id: "referenceImage",
      label: "Reference Image",
      shortLabel: "Image",
      type: "file",
      accept: "image/*",
    },
    directionPrompt,
  ],
  business: [
    {
      id: "brand",
      label: "Brand Name",
      shortLabel: "Brand",
      type: "text",
      required: true,
      placeholder: "Your company or product name",
    },
    {
      id: "offer",
      label: "Offer / CTA",
      shortLabel: "CTA",
      type: "text",
      required: true,
      placeholder: "e.g. 50% off — Order today",
    },
    {
      id: "productImage",
      label: "Product Image",
      shortLabel: "Product",
      type: "file",
      accept: "image/*",
    },
    {
      id: "adScript",
      label: "Ad Script",
      shortLabel: "Script",
      type: "textarea",
      required: true,
      placeholder: "Voiceover and on-screen copy",
    },
    directionPrompt,
  ],
  cartoon: [
    {
      id: "characters",
      label: "Characters",
      shortLabel: "Cast",
      type: "text",
      required: true,
      placeholder: "Names and looks of main characters",
    },
    {
      id: "story",
      label: "Story",
      shortLabel: "Story",
      type: "textarea",
      required: true,
      placeholder: "What happens in this episode?",
    },
    {
      id: "ageGroup",
      label: "Age Group",
      shortLabel: "Age",
      type: "text",
      placeholder: "e.g. 3–6, 7–10",
    },
    {
      id: "referenceImage",
      label: "Style Reference",
      shortLabel: "Ref",
      type: "file",
      accept: "image/*",
    },
    directionPrompt,
  ],
  story: [
    {
      id: "genre",
      label: "Genre",
      shortLabel: "Genre",
      type: "text",
      placeholder: "Drama, comedy, thriller…",
    },
    {
      id: "plot",
      label: "Plot",
      shortLabel: "Plot",
      type: "textarea",
      required: true,
      placeholder: "Beginning, conflict, and ending",
    },
    {
      id: "referenceImage",
      label: "Scene Image",
      shortLabel: "Scene",
      type: "file",
      accept: "image/*",
    },
    directionPrompt,
  ],
  podcast: [
    {
      id: "hostName",
      label: "Host Name",
      shortLabel: "Host",
      type: "text",
      required: true,
    },
    {
      id: "episodeTitle",
      label: "Episode Title",
      shortLabel: "Title",
      type: "text",
      required: true,
    },
    {
      id: "talkingPoints",
      label: "Talking Points",
      shortLabel: "Points",
      type: "textarea",
      required: true,
      placeholder: "Key topics for this clip",
    },
    {
      id: "background",
      label: "Background",
      shortLabel: "BG",
      type: "text",
      placeholder: "Studio, office, minimal",
    },
    {
      id: "coverImage",
      label: "Cover Image",
      shortLabel: "Cover",
      type: "file",
      accept: "image/*",
    },
    directionPrompt,
  ],
};

export const IMAGE_MODE_FIELDS: CategoryField[] = [
  {
    id: "sourceImage",
    label: "Source Image",
    shortLabel: "Source",
    type: "file",
    accept: "image/*",
    required: true,
    helpText: "Starting frame for image-to-video",
  },
];

export const PROMPT_MODE_FIELDS: CategoryField[] = [
  {
    id: "mainPrompt",
    label: "Visual Scene Description",
    shortLabel: "Visual Scene Description",
    type: "textarea",
    required: true,
    placeholder: "Describe the visual scene here...",
    helpText:
      "What the camera should show — action, setting, mood, and pacing. Pre-filled from your earlier prompt or lyrics when empty.",
  },
];

export const REAL_FACE_FIELDS: CategoryField[] = [
  {
    id: "faceReference",
    label: "Face Photo",
    shortLabel: "Face",
    type: "file",
    accept: "image/*",
    required: true,
    helpText: "Clear front-facing photo for identity lock",
  },
  {
    id: "faceConsent",
    label: "Face consent — type YES",
    shortLabel: "Type YES",
    type: "text",
    required: true,
    placeholder: "YES",
    helpText: "Type YES to confirm you have rights to use this face.",
  },
];

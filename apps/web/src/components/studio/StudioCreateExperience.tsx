"use client";

import { useEffect, useRef, type RefObject } from "react";
import type { GenerationMode, VideoCategory, VisualStyle } from "@rtas/shared";
import { CATEGORY_META } from "@rtas/shared";

export type SetupAccordionPhase = "mode" | "category" | "style" | "title";

const MODE_CARDS: {
  id: GenerationMode;
  title: string;
  body: string;
  badge: string;
}[] = [
  {
    id: "prompt",
    title: "Prompt → Video",
    body: "Describe the scene. RTAS composes, locks identity, and renders.",
    badge: "Most popular",
  },
  {
    id: "image",
    title: "Image → Video",
    body: "Start from a still — product, portrait, or key art — then animate.",
    badge: "Reference led",
  },
];

const STYLE_CARDS: {
  id: VisualStyle;
  title: string;
  body: string;
  facts: {
    outputStyle: string;
    quality: string;
    identity: string;
    useCases: string;
  };
  image: string;
  imageAlt: string;
}[] = [
  {
    id: "real",
    title: "Real face",
    body: "Photoreal likeness with identity lock across every shot.",
    facts: {
      outputStyle: "Photoreal human",
      quality: "Cinematic HD+",
      identity: "Maximum — face reference required",
      useCases: "Music videos, spokespeople, ads",
    },
    image: "/styles/style-real-face.jpg",
    imageAlt: "Photoreal human portrait preview for Real face style",
  },
  {
    id: "avatar",
    title: "Avatar",
    body: "Polished 3D digital presence with continuous character look.",
    facts: {
      outputStyle: "Stylized 3D avatar",
      quality: "Stylized cinema",
      identity: "Strong character continuity",
      useCases: "Brand hosts, explainers, social",
    },
    image: "/styles/style-avatar.jpg",
    imageAlt: "Stylized 3D digital avatar preview",
  },
  {
    id: "cartoon",
    title: "Cartoon",
    body: "Bold animated characters with playful, family-safe design.",
    facts: {
      outputStyle: "Animated / cartoon",
      quality: "Animated storytelling",
      identity: "Stylized cast consistency",
      useCases: "Kids content, stories, social clips",
    },
    image: "/styles/style-cartoon.jpg",
    imageAlt: "Bold cartoon character preview",
  },
];

const CATEGORY_PREVIEWS: Record<
  VideoCategory,
  { image: string; imageAlt: string }
> = {
  song: {
    image: "/categories/category-song.jpg",
    imageAlt: "Concert stage atmosphere for music videos",
  },
  business: {
    image: "/categories/category-business.jpg",
    imageAlt: "Product commercial still for business ads",
  },
  podcast: {
    image: "/categories/category-podcast.jpg",
    imageAlt: "Podcast studio microphone setup",
  },
  story: {
    image: "/categories/category-story.jpg",
    imageAlt: "Cinematic narrative night scene",
  },
  religious: {
    image: "/categories/category-religious.jpg",
    imageAlt: "Respectful mosque dusk scene for faith content",
  },
  cartoon: {
    image: "/categories/category-cartoon.jpg",
    imageAlt: "Colorful animated kids cartoon scene",
  },
};

const QUICK_STARTS: {
  id: string;
  title: string;
  body: string;
  mode: GenerationMode;
  category: VideoCategory;
  style: VisualStyle;
}[] = [
  {
    id: "music",
    title: "Music video",
    body: "Lyric-synced performance with identity lock",
    mode: "prompt",
    category: "song",
    style: "real",
  },
  {
    id: "ad",
    title: "Brand ad",
    body: "Product-forward commercial in minutes",
    mode: "image",
    category: "business",
    style: "real",
  },
  {
    id: "story",
    title: "Short story",
    body: "Narrative scenes with cinematic pacing",
    mode: "prompt",
    category: "story",
    style: "avatar",
  },
  {
    id: "kids",
    title: "Cartoon clip",
    body: "Stylized animation for kids & social",
    mode: "prompt",
    category: "cartoon",
    style: "cartoon",
  },
  {
    id: "wedding",
    title: "Wedding film",
    body: "Romantic ceremony & reception moments",
    mode: "prompt",
    category: "story",
    style: "real",
  },
  {
    id: "fashion",
    title: "Fashion lookbook",
    body: "Editorial product and runway energy",
    mode: "image",
    category: "business",
    style: "real",
  },
  {
    id: "education",
    title: "Education explainer",
    body: "Clear lesson beats for courses & schools",
    mode: "prompt",
    category: "story",
    style: "avatar",
  },
  {
    id: "gaming",
    title: "Gaming trailer",
    body: "Stylized action for game worlds & streams",
    mode: "prompt",
    category: "cartoon",
    style: "cartoon",
  },
];

/** Inspiration cards map to existing VideoCategory values only (no new enums). */
const TEMPLATES: {
  id: string;
  title: string;
  tag: string;
  mode: GenerationMode;
  category: VideoCategory;
  style: VisualStyle;
  examplePrompt: string;
  duration: string;
  notes: string;
}[] = [
  {
    id: "music-video",
    title: "Music Video",
    tag: "Music",
    mode: "prompt",
    category: "song",
    style: "real",
    examplePrompt:
      "Neon concert stage, singer locked in frame, lyric-synced cuts, sweeping crane into chorus.",
    duration: "60",
    notes: "Handheld verse → locked-off chorus; whip pans between lyric beats.",
  },
  {
    id: "islamic",
    title: "Islamic",
    tag: "Faith",
    mode: "prompt",
    category: "religious",
    style: "real",
    examplePrompt:
      "Respectful dusk mosque exterior, soft golden light, calm narration, serene atmosphere.",
    duration: "45",
    notes: "Slow push-ins, gentle dissolves; no abrupt cuts or flashy motion.",
  },
  {
    id: "business",
    title: "Business",
    tag: "Business",
    mode: "prompt",
    category: "business",
    style: "avatar",
    examplePrompt:
      "Polished brand host in a modern office, clear value proposition, confident pacing.",
    duration: "30",
    notes: "Clean medium shots, soft slide transitions, logo end-card hold.",
  },
  {
    id: "commercial",
    title: "Commercial",
    tag: "Ads",
    mode: "image",
    category: "business",
    style: "real",
    examplePrompt:
      "Product hero on reflective surface, cinematic lighting, lifestyle cutaways that sell the benefit.",
    duration: "30",
    notes: "Macro product inserts → lifestyle B-roll; smash cut to CTA.",
  },
  {
    id: "podcast",
    title: "Podcast",
    tag: "Podcast",
    mode: "prompt",
    category: "podcast",
    style: "real",
    examplePrompt:
      "Warm studio close-up of host at mic, subtle room bokeh, conversational energy.",
    duration: "60",
    notes: "Static A-cam with occasional push; soft crossfade between talking points.",
  },
  {
    id: "movie-trailer",
    title: "Movie Trailer",
    tag: "Trailer",
    mode: "prompt",
    category: "story",
    style: "real",
    examplePrompt:
      "Dark cinematic teaser, rising tension, hero silhouette, dramatic title sting.",
    duration: "45",
    notes: "Quick cuts, impact frames, sound-design pauses before title card.",
  },
  {
    id: "documentary",
    title: "Documentary",
    tag: "Doc",
    mode: "prompt",
    category: "story",
    style: "real",
    examplePrompt:
      "Observational landscape open, interview-style presence, thoughtful voiceover mood.",
    duration: "90",
    notes: "Slow pans, archival-feel dissolves, lingering establishing shots.",
  },
  {
    id: "wedding",
    title: "Wedding",
    tag: "Wedding",
    mode: "prompt",
    category: "story",
    style: "real",
    examplePrompt:
      "Soft romantic ceremony light, vows moment, golden-hour couple walk.",
    duration: "60",
    notes: "Shallow DOF, gentle steadicam, warm cross-dissolves.",
  },
  {
    id: "fashion",
    title: "Fashion",
    tag: "Fashion",
    mode: "image",
    category: "business",
    style: "real",
    examplePrompt:
      "Editorial runway energy, fabric motion, confident walk, high-fashion lighting.",
    duration: "30",
    notes: "Tracking shots along walk; hard cuts to detail inserts.",
  },
  {
    id: "education",
    title: "Education",
    tag: "Education",
    mode: "prompt",
    category: "story",
    style: "avatar",
    examplePrompt:
      "Friendly explainer host, clear lesson beats, on-screen concept moments.",
    duration: "45",
    notes: "Static teaching frame with soft zooms; wipe between chapters.",
  },
  {
    id: "gaming",
    title: "Gaming",
    tag: "Gaming",
    mode: "prompt",
    category: "cartoon",
    style: "cartoon",
    examplePrompt:
      "Bold stylized boss reveal, dynamic camera orbit, high-energy trailer vibe.",
    duration: "30",
    notes: "Orbit + snap zooms; glitch-style transition into logo.",
  },
  {
    id: "travel",
    title: "Travel",
    tag: "Travel",
    mode: "prompt",
    category: "story",
    style: "real",
    examplePrompt:
      "Sunrise city overlook, traveler silhouette, wanderlust montage energy.",
    duration: "45",
    notes: "Drone-style opens, match cuts on motion, warm color grade.",
  },
  {
    id: "kids",
    title: "Kids",
    tag: "Kids",
    mode: "prompt",
    category: "cartoon",
    style: "cartoon",
    examplePrompt:
      "Bright playful cartoon world, friendly characters, simple joyful story beat.",
    duration: "30",
    notes: "Bounce zooms, colorful pops, soft star wipe transitions.",
  },
  {
    id: "story",
    title: "Story",
    tag: "Story",
    mode: "prompt",
    category: "story",
    style: "avatar",
    examplePrompt:
      "Narrative short with emotional arc, character close-ups, cinematic pacing.",
    duration: "60",
    notes: "Motivated camera moves; motivated dissolves at act turns.",
  },
  {
    id: "short-film",
    title: "Short Film",
    tag: "Film",
    mode: "prompt",
    category: "story",
    style: "real",
    examplePrompt:
      "Intimate short-film scene, naturalistic lighting, quiet dramatic tension.",
    duration: "90",
    notes: "Longer takes, subtle push-ins, cut on glance / breath.",
  },
  {
    id: "youtube",
    title: "YouTube",
    tag: "YouTube",
    mode: "prompt",
    category: "business",
    style: "real",
    examplePrompt:
      "Creator talking-head with punchy hook, B-roll inserts, clear end-screen CTA.",
    duration: "60",
    notes: "Jump cuts on speech; pattern interrupts every 8–12s.",
  },
  {
    id: "tiktok",
    title: "TikTok",
    tag: "TikTok",
    mode: "prompt",
    category: "cartoon",
    style: "cartoon",
    examplePrompt:
      "Vertical-first hook in first second, bold motion, trend-ready visual gag.",
    duration: "15",
    notes: "Snap zooms, text-safe framing, beat-synced hard cuts.",
  },
  {
    id: "instagram",
    title: "Instagram",
    tag: "Instagram",
    mode: "image",
    category: "business",
    style: "real",
    examplePrompt:
      "Aesthetic product reel, clean lifestyle frames, soft brand finish.",
    duration: "30",
    notes: "Smooth steadicam; fade-to-brand color hold at end.",
  },
  {
    id: "facebook",
    title: "Facebook",
    tag: "Facebook",
    mode: "prompt",
    category: "business",
    style: "avatar",
    examplePrompt:
      "Friendly brand message for feed, clear offer, community-first tone.",
    duration: "30",
    notes: "Centered framing for mute autoplay; caption-friendly holds.",
  },
];

export type TemplateApplyOptions = {
  mode: GenerationMode;
  category: VideoCategory;
  style: VisualStyle;
  title?: string;
  directionPrompt?: string;
  duration?: string;
  notes?: string;
};

type StudioCreateExperienceProps = {
  mode: GenerationMode | null;
  category: VideoCategory | null;
  visualStyle: VisualStyle | null;
  title: string;
  setupPhase: SetupAccordionPhase;
  disabled?: boolean;
  onSetupPhaseChange: (phase: SetupAccordionPhase) => void;
  onModeSelect: (mode: GenerationMode) => void;
  onCategorySelect: (category: VideoCategory) => void;
  onStyleSelect: (style: VisualStyle) => void;
  onTitleChange: (value: string) => void;
  onQuickStart: (opts: {
    mode: GenerationMode;
    category: VideoCategory;
    style: VisualStyle;
  }) => void;
  onTemplateApply?: (opts: TemplateApplyOptions) => void;
  titleError?: string;
  titleFieldId: string;
};

function sectionClass(phase: SetupAccordionPhase, active: SetupAccordionPhase) {
  return `studio-picker-section studio-accordion-section${
    active === phase ? " is-expanded" : " is-collapsed"
  }`;
}

export function StudioCreateExperience({
  mode,
  category,
  visualStyle,
  title,
  setupPhase,
  disabled = false,
  onSetupPhaseChange,
  onModeSelect,
  onCategorySelect,
  onStyleSelect,
  onTitleChange,
  onQuickStart,
  onTemplateApply,
  titleError,
  titleFieldId,
}: StudioCreateExperienceProps) {
  const modeRef = useRef<HTMLElement>(null);
  const categoryRef = useRef<HTMLElement>(null);
  const styleRef = useRef<HTMLElement>(null);
  const titleRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const map: Record<SetupAccordionPhase, RefObject<HTMLElement | null>> = {
      mode: modeRef,
      category: categoryRef,
      style: styleRef,
      title: titleRef,
    };
    const target = map[setupPhase].current;
    if (!target) return;
    const timer = window.setTimeout(() => {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 80);
    return () => window.clearTimeout(timer);
  }, [setupPhase]);

  const modeLabel = MODE_CARDS.find((c) => c.id === mode)?.title;
  const categoryLabel = category ? CATEGORY_META[category].shortLabel : null;
  const styleLabel = STYLE_CARDS.find((c) => c.id === visualStyle)?.title;

  return (
    <div className="studio-create-experience">
      {!mode ? (
        <section className="studio-welcome" aria-labelledby="studio-welcome-title">
          <p className="studio-welcome__eyebrow">AI Studio</p>
          <h2 id="studio-welcome-title" className="studio-welcome__title">
            What are we creating today?
          </h2>
          <p className="studio-welcome__lead">
            Compose with identity lock, render in the cloud, and publish with commercial-ready
            masters — all in one premium workspace.
          </p>

          <div className="studio-quick-grid" aria-label="Quick start">
            {QUICK_STARTS.map((item) => (
              <button
                key={item.id}
                type="button"
                className="studio-quick-card"
                disabled={disabled}
                onClick={() =>
                  onQuickStart({
                    mode: item.mode,
                    category: item.category,
                    style: item.style,
                  })
                }
              >
                <span className="studio-quick-card__title">{item.title}</span>
                <span className="studio-quick-card__body">{item.body}</span>
              </button>
            ))}
          </div>
        </section>
      ) : null}

      <section
        ref={modeRef}
        className={sectionClass("mode", setupPhase)}
        aria-labelledby="studio-mode-title"
      >
        <div className="studio-picker-section__head studio-accordion-section__head">
          <div className="studio-accordion-section__title-row">
            <h3 id="studio-mode-title">1 · Choose mode</h3>
            {mode && setupPhase !== "mode" && modeLabel ? (
              <button
                type="button"
                className="studio-accordion-summary-chip"
                disabled={disabled}
                onClick={() => onSetupPhaseChange("mode")}
              >
                {modeLabel}
              </button>
            ) : null}
          </div>
          {setupPhase === "mode" ? <p>How your video begins</p> : null}
        </div>
        <div className="studio-accordion-section__panel" aria-hidden={setupPhase !== "mode"}>
          <div className="studio-mode-grid">
            {MODE_CARDS.map((card) => (
              <button
                key={card.id}
                type="button"
                className={`studio-mode-card${mode === card.id ? " is-active" : ""}`}
                disabled={disabled}
                aria-pressed={mode === card.id}
                tabIndex={setupPhase === "mode" ? undefined : -1}
                onClick={() => onModeSelect(card.id)}
              >
                <span className="studio-mode-card__badge">{card.badge}</span>
                <span className="studio-mode-card__title">{card.title}</span>
                <span className="studio-mode-card__body">{card.body}</span>
              </button>
            ))}
          </div>
        </div>
      </section>

      {mode ? (
        <section
          ref={categoryRef}
          className={sectionClass("category", setupPhase)}
          aria-labelledby="studio-category-title"
        >
          <div className="studio-picker-section__head studio-accordion-section__head">
            <div className="studio-accordion-section__title-row">
              <h3 id="studio-category-title">2 · Category</h3>
              {category && setupPhase !== "category" && categoryLabel ? (
                <button
                  type="button"
                  className="studio-accordion-summary-chip"
                  disabled={disabled}
                  onClick={() => onSetupPhaseChange("category")}
                >
                  {categoryLabel}
                </button>
              ) : null}
            </div>
            {setupPhase === "category" ? (
              <p>Pick the format that matches your brief</p>
            ) : null}
          </div>
          <div
            className="studio-accordion-section__panel"
            aria-hidden={setupPhase !== "category"}
          >
            <div className="studio-category-grid">
              {(Object.keys(CATEGORY_META) as VideoCategory[]).map((c) => {
                const preview = CATEGORY_PREVIEWS[c];
                return (
                  <button
                    key={c}
                    type="button"
                    className={`studio-category-card${category === c ? " is-active" : ""}`}
                    disabled={disabled}
                    aria-pressed={category === c}
                    title={CATEGORY_META[c].description}
                    tabIndex={setupPhase === "category" ? undefined : -1}
                    onClick={() => onCategorySelect(c)}
                  >
                    <span className="studio-category-card__media" aria-hidden>
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={preview.image}
                        alt=""
                        className="studio-category-card__image"
                        width={360}
                        height={480}
                        loading="lazy"
                        decoding="async"
                      />
                    </span>
                    <span className="studio-category-card__label">
                      {CATEGORY_META[c].shortLabel}
                    </span>
                    <span className="studio-category-card__desc">
                      {CATEGORY_META[c].description}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </section>
      ) : null}

      {mode && category ? (
        <section
          ref={styleRef}
          className={sectionClass("style", setupPhase)}
          aria-labelledby="studio-style-title"
        >
          <div className="studio-picker-section__head studio-accordion-section__head">
            <div className="studio-accordion-section__title-row">
              <h3 id="studio-style-title">3 · Visual style</h3>
              {visualStyle && setupPhase !== "style" && styleLabel ? (
                <button
                  type="button"
                  className="studio-accordion-summary-chip"
                  disabled={disabled}
                  onClick={() => onSetupPhaseChange("style")}
                >
                  {styleLabel}
                </button>
              ) : null}
            </div>
            {setupPhase === "style" ? (
              <p>Identity and look for the whole project</p>
            ) : null}
          </div>
          <div
            className="studio-accordion-section__panel"
            aria-hidden={setupPhase !== "style"}
          >
            <div className="studio-style-grid">
              {STYLE_CARDS.map((card) => (
                <button
                  key={card.id}
                  type="button"
                  className={`studio-style-card${visualStyle === card.id ? " is-active" : ""}`}
                  disabled={disabled}
                  aria-pressed={visualStyle === card.id}
                  tabIndex={setupPhase === "style" ? undefined : -1}
                  onClick={() => onStyleSelect(card.id)}
                >
                  <span className="studio-style-card__swatch" data-style={card.id}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={card.image}
                      alt={card.imageAlt}
                      className="studio-style-card__image"
                      width={480}
                      height={300}
                      loading="lazy"
                      decoding="async"
                    />
                  </span>
                  <span className="studio-style-card__title">{card.title}</span>
                  <span className="studio-style-card__body">{card.body}</span>
                  <dl className="studio-style-card__facts">
                    <div className="studio-style-card__fact">
                      <dt>Output style</dt>
                      <dd>{card.facts.outputStyle}</dd>
                    </div>
                    <div className="studio-style-card__fact">
                      <dt>Quality</dt>
                      <dd>{card.facts.quality}</dd>
                    </div>
                    <div className="studio-style-card__fact">
                      <dt>Identity</dt>
                      <dd>{card.facts.identity}</dd>
                    </div>
                    <div className="studio-style-card__fact">
                      <dt>Best for</dt>
                      <dd>{card.facts.useCases}</dd>
                    </div>
                  </dl>
                </button>
              ))}
            </div>
          </div>
        </section>
      ) : null}

      {mode && category && visualStyle ? (
        <section
          ref={titleRef}
          className={sectionClass("title", setupPhase)}
          aria-labelledby="studio-title-heading"
        >
          <div className="studio-picker-section__head studio-accordion-section__head">
            <div className="studio-accordion-section__title-row">
              <h3 id="studio-title-heading">4 · Project title</h3>
              {title.trim().length >= 2 && setupPhase !== "title" ? (
                <button
                  type="button"
                  className="studio-accordion-summary-chip"
                  disabled={disabled}
                  onClick={() => onSetupPhaseChange("title")}
                >
                  {title.trim()}
                </button>
              ) : null}
            </div>
            {setupPhase === "title" ? (
              <p>Shown in your library and preview player</p>
            ) : null}
          </div>
          <div
            className="studio-accordion-section__panel"
            aria-hidden={setupPhase !== "title"}
          >
            <div className="studio-title-field">
              <label htmlFor={titleFieldId}>Video title</label>
              <input
                id={titleFieldId}
                type="text"
                className={titleError ? "field-error" : undefined}
                placeholder="e.g. Midnight Drive — Official Video"
                value={title}
                onChange={(e) => onTitleChange(e.target.value)}
                disabled={disabled}
                tabIndex={setupPhase === "title" ? undefined : -1}
                aria-invalid={Boolean(titleError)}
              />
              {titleError ? (
                <p className="field-error">{titleError}</p>
              ) : (
                <p className="help">This exact name appears in Your videos.</p>
              )}
            </div>
          </div>
        </section>
      ) : null}

      {!mode ? (
        <section className="studio-inspiration" aria-labelledby="studio-inspiration-title">
          <div className="studio-picker-section__head">
            <h3 id="studio-inspiration-title">Templates & inspiration</h3>
            <p>
              Music, faith, social, film, and more — each maps to an existing Studio category
            </p>
          </div>
          <div className="studio-template-grid">
            {TEMPLATES.map((tpl) => (
              <button
                key={tpl.id}
                type="button"
                className="studio-template-card"
                disabled={disabled}
                onClick={() => {
                  onQuickStart({
                    mode: tpl.mode,
                    category: tpl.category,
                    style: tpl.style,
                  });
                  onTemplateApply?.({
                    mode: tpl.mode,
                    category: tpl.category,
                    style: tpl.style,
                    title: tpl.title,
                    directionPrompt: `${tpl.examplePrompt}\n\nCamera / transitions: ${tpl.notes}`,
                    duration: tpl.duration,
                    notes: tpl.notes,
                  });
                }}
              >
                <span className="studio-template-card__tag">{tpl.tag}</span>
                <h4>{tpl.title}</h4>
                <p className="studio-template-card__body">{tpl.examplePrompt}</p>
                <p className="studio-template-card__notes">{tpl.notes}</p>
                <span className="studio-template-card__duration">{tpl.duration}s</span>
              </button>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

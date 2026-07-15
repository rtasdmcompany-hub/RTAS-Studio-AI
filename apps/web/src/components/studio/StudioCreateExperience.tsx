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

/** Curated project picks — maps only to existing VideoCategory / VisualStyle. */
const PROJECT_CARDS: {
  id: string;
  title: string;
  tag: string;
  body: string;
  mode: GenerationMode;
  category: VideoCategory;
  suggestedStyle: VisualStyle;
  examplePrompt?: string;
  duration?: string;
  notes?: string;
}[] = [
  {
    id: "music-video",
    title: "Music Video",
    tag: "Music",
    body: "Lyric-synced performance with identity lock",
    mode: "prompt",
    category: "song",
    suggestedStyle: "real",
    examplePrompt:
      "Neon concert stage, singer locked in frame, lyric-synced cuts, sweeping crane into chorus.",
    duration: "60",
    notes: "Handheld verse → locked-off chorus; whip pans between lyric beats.",
  },
  {
    id: "brand-ad",
    title: "Brand ad",
    tag: "Ads",
    body: "Product-forward commercial in minutes",
    mode: "image",
    category: "business",
    suggestedStyle: "real",
    examplePrompt:
      "Product hero on reflective surface, cinematic lighting, lifestyle cutaways that sell the benefit.",
    duration: "30",
    notes: "Macro product inserts → lifestyle B-roll; smash cut to CTA.",
  },
  {
    id: "short-story",
    title: "Short story",
    tag: "Film",
    body: "Narrative scenes with cinematic pacing",
    mode: "prompt",
    category: "story",
    suggestedStyle: "avatar",
    examplePrompt: "Cinematic short story with emotional beats and locked character continuity.",
    duration: "45",
  },
  {
    id: "cartoon-clip",
    title: "Cartoon clip",
    tag: "Kids",
    body: "Stylized animation for kids & social",
    mode: "prompt",
    category: "cartoon",
    suggestedStyle: "cartoon",
    examplePrompt: "Playful cartoon characters in a colorful world, family-safe energy.",
    duration: "30",
  },
  {
    id: "islamic",
    title: "Faith film",
    tag: "Faith",
    body: "Respectful dusk atmosphere and calm narration",
    mode: "prompt",
    category: "religious",
    suggestedStyle: "real",
    examplePrompt:
      "Respectful dusk mosque exterior, soft golden light, calm narration, serene atmosphere.",
    duration: "45",
    notes: "Slow push-ins, gentle dissolves; no abrupt cuts or flashy motion.",
  },
  {
    id: "podcast",
    title: "Podcast",
    tag: "Audio",
    body: "Host-forward talk with clean studio framing",
    mode: "prompt",
    category: "podcast",
    suggestedStyle: "real",
    examplePrompt: "Warm podcast studio, host locked in medium shot, soft key light, calm pacing.",
    duration: "60",
  },
  {
    id: "wedding",
    title: "Wedding film",
    tag: "Story",
    body: "Romantic ceremony & reception moments",
    mode: "prompt",
    category: "story",
    suggestedStyle: "real",
    examplePrompt: "Romantic wedding film — soft golden hour, emotional close-ups, elegant pacing.",
    duration: "60",
  },
  {
    id: "fashion",
    title: "Fashion lookbook",
    tag: "Ads",
    body: "Editorial product and runway energy",
    mode: "image",
    category: "business",
    suggestedStyle: "real",
    examplePrompt: "Editorial fashion lookbook, confident walk cycles, crisp product inserts.",
    duration: "30",
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

function SummaryChip({
  label,
  value,
  onEdit,
  disabled,
}: {
  label: string;
  value: string;
  onEdit: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      className="studio-wizard-summary-chip"
      disabled={disabled}
      onClick={onEdit}
    >
      <span className="studio-wizard-summary-chip__label">{label}</span>
      <span className="studio-wizard-summary-chip__value">{value}</span>
      <span className="studio-wizard-summary-chip__edit" aria-hidden>
        Edit
      </span>
    </button>
  );
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
  const activeRef = useRef<HTMLElement>(null);

  // Map setup phases to guided steps: project → style → title
  const activeStep: "project" | "style" | "title" =
    setupPhase === "title"
      ? "title"
      : setupPhase === "style" || (mode && category && !visualStyle)
        ? "style"
        : "project";

  useEffect(() => {
    const target = activeRef.current;
    if (!target) return;
    const timer = window.setTimeout(() => {
      target.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }, 60);
    return () => window.clearTimeout(timer);
  }, [activeStep, setupPhase]);

  const modeLabel = MODE_CARDS.find((c) => c.id === mode)?.title;
  const categoryLabel = category ? CATEGORY_META[category].shortLabel : null;
  const styleLabel = STYLE_CARDS.find((c) => c.id === visualStyle)?.title;
  const projectSummary =
    categoryLabel && modeLabel ? `${categoryLabel} · ${modeLabel}` : categoryLabel || modeLabel;

  const applyProject = (card: (typeof PROJECT_CARDS)[number]) => {
    onQuickStart({
      mode: card.mode,
      category: card.category,
      style: card.suggestedStyle,
    });
    onTemplateApply?.({
      mode: card.mode,
      category: card.category,
      style: card.suggestedStyle,
      title: card.title,
      directionPrompt: card.examplePrompt
        ? `${card.examplePrompt}${card.notes ? `\n\nCamera / transitions: ${card.notes}` : ""}`
        : undefined,
      duration: card.duration,
      notes: card.notes,
    });
  };

  return (
    <div className="studio-create-experience studio-create-experience--guided">
      {(mode || category || visualStyle || title.trim()) && (
        <div className="studio-wizard-summary" aria-label="Completed setup steps">
          {projectSummary ? (
            <SummaryChip
              label="1 · Project"
              value={projectSummary}
              disabled={disabled}
              onEdit={() => {
                onSetupPhaseChange("mode");
              }}
            />
          ) : null}
          {styleLabel ? (
            <SummaryChip
              label="2 · Style"
              value={styleLabel}
              disabled={disabled}
              onEdit={() => onSetupPhaseChange("style")}
            />
          ) : null}
          {title.trim().length >= 2 && activeStep !== "title" ? (
            <SummaryChip
              label="3 · Title"
              value={title.trim()}
              disabled={disabled}
              onEdit={() => onSetupPhaseChange("title")}
            />
          ) : null}
        </div>
      )}

      {activeStep === "project" ? (
        <section
          ref={activeRef as RefObject<HTMLElement>}
          className="studio-guided-step is-active"
          aria-labelledby="studio-project-title"
        >
          <header className="studio-guided-step__head">
            <p className="studio-guided-step__eyebrow">Step 1 of 3</p>
            <h2 id="studio-project-title" className="studio-guided-step__title">
              Choose project
            </h2>
            <p className="studio-guided-step__lead">
              Pick a starting point. You&apos;ll confirm style next — one step at a time.
            </p>
          </header>

          <div className="studio-project-grid" role="list">
            {PROJECT_CARDS.map((card) => (
              <button
                key={card.id}
                type="button"
                className="studio-project-card"
                disabled={disabled}
                role="listitem"
                onClick={() => applyProject(card)}
              >
                <span className="studio-project-card__media" aria-hidden>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={CATEGORY_PREVIEWS[card.category].image}
                    alt=""
                    width={360}
                    height={240}
                    loading="lazy"
                    decoding="async"
                  />
                </span>
                <span className="studio-project-card__tag">{card.tag}</span>
                <span className="studio-project-card__title">{card.title}</span>
                <span className="studio-project-card__body">{card.body}</span>
              </button>
            ))}
          </div>

          <details className="studio-guided-advanced">
            <summary>Custom mode & category</summary>
            <div className="studio-guided-advanced__body">
              <p className="studio-guided-advanced__hint">Or build from scratch:</p>
              <div className="studio-mode-grid">
                {MODE_CARDS.map((card) => (
                  <button
                    key={card.id}
                    type="button"
                    className={`studio-mode-card${mode === card.id ? " is-active" : ""}`}
                    disabled={disabled}
                    aria-pressed={mode === card.id}
                    onClick={() => onModeSelect(card.id)}
                  >
                    <span className="studio-mode-card__badge">{card.badge}</span>
                    <span className="studio-mode-card__title">{card.title}</span>
                    <span className="studio-mode-card__body">{card.body}</span>
                  </button>
                ))}
              </div>
              {mode ? (
                <div className="studio-category-grid studio-category-grid--compact">
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
                      </button>
                    );
                  })}
                </div>
              ) : null}
            </div>
          </details>
        </section>
      ) : null}

      {activeStep === "style" && mode && category ? (
        <section
          ref={activeRef as RefObject<HTMLElement>}
          className="studio-guided-step is-active"
          aria-labelledby="studio-style-title"
        >
          <header className="studio-guided-step__head">
            <p className="studio-guided-step__eyebrow">Step 2 of 3</p>
            <h2 id="studio-style-title" className="studio-guided-step__title">
              Choose style
            </h2>
            <p className="studio-guided-step__lead">
              Identity and look for the whole project.
            </p>
          </header>
          <div className="studio-style-grid">
            {STYLE_CARDS.map((card) => (
              <button
                key={card.id}
                type="button"
                className={`studio-style-card${visualStyle === card.id ? " is-active" : ""}`}
                disabled={disabled}
                aria-pressed={visualStyle === card.id}
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
        </section>
      ) : null}

      {activeStep === "title" && mode && category && visualStyle ? (
        <section
          ref={activeRef as RefObject<HTMLElement>}
          className="studio-guided-step is-active"
          aria-labelledby="studio-title-heading"
        >
          <header className="studio-guided-step__head">
            <p className="studio-guided-step__eyebrow">Step 3 of 3</p>
            <h2 id="studio-title-heading" className="studio-guided-step__title">
              Name your project
            </h2>
            <p className="studio-guided-step__lead">
              Shown in your library and preview player. Then continue to character, product, voice,
              and prompt.
            </p>
          </header>
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
              aria-invalid={Boolean(titleError)}
              autoFocus
            />
            {titleError ? (
              <p className="field-error">{titleError}</p>
            ) : (
              <p className="help">This exact name appears in Your videos.</p>
            )}
          </div>
        </section>
      ) : null}
    </div>
  );
}

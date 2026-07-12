"use client";

import type { GenerationMode, VideoCategory, VisualStyle } from "@rtas/shared";
import { CATEGORY_META } from "@rtas/shared";

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
  image: string;
  imageAlt: string;
}[] = [
  {
    id: "real",
    title: "Real face",
    body: "Identity lock for consistent likeness across every shot.",
    image: "/styles/style-real-face.jpg",
    imageAlt: "Example of a realistic human face look for identity-locked video",
  },
  {
    id: "avatar",
    title: "Avatar",
    body: "Stylized digital presence with cinematic continuity.",
    image: "/styles/style-avatar.jpg",
    imageAlt: "Example of a stylized digital avatar character look",
  },
  {
    id: "cartoon",
    title: "Cartoon",
    body: "Animated storytelling with bold character design.",
    image: "/styles/style-cartoon.jpg",
    imageAlt: "Example of a bold cartoon character look for animated stories",
  },
];

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
];

const TEMPLATES = [
  { id: "neon-rap", title: "Neon concert", tag: "Music" },
  { id: "product-hero", title: "Product hero", tag: "Commercial" },
  { id: "talking-head", title: "Talking head", tag: "Podcast" },
  { id: "faith-film", title: "Faith cinema", tag: "Religious" },
  { id: "kids-world", title: "Kids world", tag: "Cartoon" },
  { id: "brand-story", title: "Brand story", tag: "Business" },
];

type StudioCreateExperienceProps = {
  mode: GenerationMode | null;
  category: VideoCategory | null;
  visualStyle: VisualStyle | null;
  title: string;
  disabled?: boolean;
  onModeSelect: (mode: GenerationMode) => void;
  onCategorySelect: (category: VideoCategory) => void;
  onStyleSelect: (style: VisualStyle) => void;
  onTitleChange: (value: string) => void;
  onQuickStart: (opts: {
    mode: GenerationMode;
    category: VideoCategory;
    style: VisualStyle;
  }) => void;
  titleError?: string;
  titleFieldId: string;
};

export function StudioCreateExperience({
  mode,
  category,
  visualStyle,
  title,
  disabled = false,
  onModeSelect,
  onCategorySelect,
  onStyleSelect,
  onTitleChange,
  onQuickStart,
  titleError,
  titleFieldId,
}: StudioCreateExperienceProps) {
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
        className="studio-picker-section"
        aria-labelledby="studio-mode-title"
      >
        <div className="studio-picker-section__head">
          <h3 id="studio-mode-title">1 · Choose mode</h3>
          <p>How your video begins</p>
        </div>
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
      </section>

      {mode ? (
        <section className="studio-picker-section" aria-labelledby="studio-category-title">
          <div className="studio-picker-section__head">
            <h3 id="studio-category-title">2 · Category</h3>
            <p>Pick the format that matches your brief</p>
          </div>
          <div className="studio-category-grid">
            {(Object.keys(CATEGORY_META) as VideoCategory[]).map((c) => (
              <button
                key={c}
                type="button"
                className={`studio-category-card${category === c ? " is-active" : ""}`}
                disabled={disabled}
                aria-pressed={category === c}
                title={CATEGORY_META[c].description}
                onClick={() => onCategorySelect(c)}
              >
                <span className="studio-category-card__label">
                  {CATEGORY_META[c].shortLabel}
                </span>
                <span className="studio-category-card__desc">
                  {CATEGORY_META[c].description}
                </span>
              </button>
            ))}
          </div>
        </section>
      ) : null}

      {mode && category ? (
        <section className="studio-picker-section" aria-labelledby="studio-style-title">
          <div className="studio-picker-section__head">
            <h3 id="studio-style-title">3 · Visual style</h3>
            <p>Identity and look for the whole project</p>
          </div>
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
              </button>
            ))}
          </div>
        </section>
      ) : null}

      {mode && category && visualStyle ? (
        <section className="studio-picker-section" aria-labelledby="studio-title-heading">
          <div className="studio-picker-section__head">
            <h3 id="studio-title-heading">4 · Project title</h3>
            <p>Shown in your library and preview player</p>
          </div>
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
            />
            {titleError ? (
              <p className="field-error">{titleError}</p>
            ) : (
              <p className="help">This exact name appears in Your videos.</p>
            )}
          </div>
        </section>
      ) : null}

      {!mode ? (
        <section className="studio-inspiration" aria-labelledby="studio-inspiration-title">
          <div className="studio-picker-section__head">
            <h3 id="studio-inspiration-title">Templates & inspiration</h3>
            <p>Start from a proven composition, then make it yours</p>
          </div>
          <div className="studio-template-grid">
            {TEMPLATES.map((tpl) => (
              <article key={tpl.id} className="studio-template-card">
                <span className="studio-template-card__tag">{tpl.tag}</span>
                <h4>{tpl.title}</h4>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

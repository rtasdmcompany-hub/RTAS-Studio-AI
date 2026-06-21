"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef } from "react";
import { PRODUCT_NAME } from "@rtas/shared";
import {
  CATEGORY_GUIDES,
  STUDIO_FLOW,
  UNIVERSAL_STEPS,
} from "@/lib/how-to-use-content";

function GuideMedia({
  media,
}: {
  media: { type: "video" | "image"; src: string; alt: string };
}) {
  const ref = useRef<HTMLVideoElement>(null);

  const play = useCallback(() => {
    const video = ref.current;
    if (!video) return;
    void video.play().catch(() => {});
  }, []);

  useEffect(() => {
    play();
  }, [media.src, play]);

  if (media.type === "video") {
    return (
      <video
        ref={ref}
        src={media.src}
        autoPlay
        muted
        loop
        playsInline
        preload="metadata"
        className="rtas-howto-media__video"
        aria-label={media.alt}
        onLoadedData={play}
      />
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={media.src} alt={media.alt} className="rtas-howto-media__img" />
  );
}

export function HowToUseGuide() {
  return (
    <article className="rtas-howto-page video-content-panel">
      <header className="rtas-howto-page__hero">
        <p className="rtas-eyebrow">User guide</p>
        <h1>How to use {PRODUCT_NAME}</h1>
        <p className="rtas-howto-page__lead">
          Step-by-step instructions with visuals for Song, Religious, Cartoon, Podcast,
          Business, and Story videos. Follow along and create in Studio.
        </p>
        <div className="rtas-howto-page__actions">
          <Link href="/studio" className="rtas-btn-lavender">
            Open Studio <span aria-hidden>→</span>
          </Link>
          <a href="#categories" className="rtas-btn-ghost">
            Jump to categories
          </a>
        </div>
      </header>

      <section className="rtas-howto-section" aria-labelledby="howto-universal">
        <h2 id="howto-universal">Quick start — 5 steps</h2>
        <p className="rtas-howto-section__intro">
          These steps apply to every category. Start here, then open the guide for your
          video type below.
        </p>
        <ol className="rtas-howto-steps">
          {UNIVERSAL_STEPS.map((step) => (
            <li key={step.num} className="rtas-howto-step">
              <span className="rtas-howto-step__num" aria-hidden>
                {step.num}
              </span>
              <div className="rtas-howto-step__body">
                <h3>{step.title}</h3>
                <p>{step.detail}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="rtas-howto-section" aria-labelledby="howto-flow">
        <h2 id="howto-flow">Studio setup flow</h2>
        <p className="rtas-howto-section__intro">
          After opening Studio, complete each section in order. The next section appears
          when the current one is complete.
        </p>
        <div className="rtas-howto-flow">
          {STUDIO_FLOW.map((item, index) => (
            <div key={item.label} className="rtas-howto-flow__item">
              <span className="rtas-howto-flow__badge">{index + 1}</span>
              <div>
                <strong>{item.label}</strong>
                <p>{item.options}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="rtas-howto-callout">
          <strong>Real style tip:</strong> To appear on screen yourself, upload a clear
          front-facing photo and type <code>YES</code> in the consent field.
        </div>
      </section>

      <nav className="rtas-howto-jump" id="categories" aria-label="Category guides">
        <h2>Category guides</h2>
        <ul className="rtas-howto-jump__list">
          {CATEGORY_GUIDES.map((guide) => (
            <li key={guide.id}>
              <a href={`#guide-${guide.id}`}>{guide.title}</a>
            </li>
          ))}
        </ul>
      </nav>

      {CATEGORY_GUIDES.map((guide) => (
        <section
          key={guide.id}
          id={`guide-${guide.id}`}
          className="rtas-howto-category"
          aria-labelledby={`guide-title-${guide.id}`}
        >
          <div className="rtas-howto-category__grid">
            <div className="rtas-howto-media">
              <GuideMedia media={guide.media} />
              <span className="rtas-howto-media__label">{guide.title}</span>
            </div>

            <div className="rtas-howto-category__content">
              <h2 id={`guide-title-${guide.id}`}>{guide.title}</h2>
              <p>{guide.summary}</p>

              <h3>Best for</h3>
              <ul className="rtas-howto-tags">
                {guide.bestFor.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>

              <div className="rtas-howto-reco">
                <h3>Recommended settings</h3>
                <dl>
                  <div>
                    <dt>Mode</dt>
                    <dd>{guide.recommended.mode}</dd>
                  </div>
                  <div>
                    <dt>Visual style</dt>
                    <dd>{guide.recommended.visualStyle}</dd>
                  </div>
                  <div>
                    <dt>Length</dt>
                    <dd>{guide.recommended.length}</dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>

          <div className="rtas-howto-category__steps">
            <h3>Step-by-step for this category</h3>
            <ol className="rtas-howto-mini-steps">
              {guide.steps.map((step, index) => (
                <li key={step.title}>
                  <span className="rtas-howto-mini-steps__num">{index + 1}</span>
                  <div>
                    <strong>{step.title}</strong>
                    <p>{step.detail}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>

          <div className="rtas-howto-tips">
            <h3>Tips</h3>
            <ul>
              {guide.tips.map((tip) => (
                <li key={tip}>{tip}</li>
              ))}
            </ul>
          </div>

          <Link href="/studio" className="rtas-btn-lavender rtas-howto-category__cta">
            Create in Studio →
          </Link>
        </section>
      ))}

      <footer className="rtas-howto-page__footer">
        <h2>Need help?</h2>
        <p>
          Use live chat in the bottom-right corner or email{" "}
          <a href="mailto:support@rtasdigital.com">support@rtasdigital.com</a>.
        </p>
        <div className="rtas-howto-page__actions">
          <Link href="/pricing" className="rtas-btn-ghost">
            View pricing and credits
          </Link>
          <Link href="/studio" className="rtas-btn-lavender">
            Start creating
          </Link>
        </div>
      </footer>
    </article>
  );
}

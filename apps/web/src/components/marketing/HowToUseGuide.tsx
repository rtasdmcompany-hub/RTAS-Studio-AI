"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ButtonLink } from "@rtas/ui";
import {
  CATEGORY_GUIDES,
  STUDIO_FLOW,
  UNIVERSAL_STEPS,
} from "@/lib/how-to-use-content";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

function GuideMedia({
  media,
}: {
  media: { type: "video" | "image"; src: string; alt: string };
}) {
  const ref = useRef<HTMLVideoElement>(null);
  const [shouldLoad, setShouldLoad] = useState(false);

  const play = useCallback(() => {
    const video = ref.current;
    if (!video) return;
    void video.play().catch(() => {});
  }, []);

  useEffect(() => {
    const node = ref.current;
    if (!node && media.type === "video") return;

    if (typeof IntersectionObserver === "undefined") {
      setShouldLoad(true);
      return;
    }

    const target = media.type === "video" ? ref.current : null;
    if (!target) {
      setShouldLoad(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setShouldLoad(true);
          observer.disconnect();
        }
      },
      { rootMargin: "200px", threshold: 0.05 }
    );
    observer.observe(target);
    return () => observer.disconnect();
  }, [media.type]);

  useEffect(() => {
    if (shouldLoad && media.type === "video") play();
  }, [media.src, shouldLoad, media.type, play]);

  if (media.type === "video") {
    return (
      <video
        ref={ref}
        src={shouldLoad ? media.src : undefined}
        autoPlay={shouldLoad}
        muted
        loop
        playsInline
        preload="none"
        className="rtas-howto-media__video"
        aria-label={media.alt}
        onLoadedData={play}
      />
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={media.src}
      alt={media.alt}
      className="rtas-howto-media__img"
      loading="lazy"
      decoding="async"
    />
  );
}

export function HowToUseGuide() {
  return (
    <InnerPageContainer>
        <InnerPageSection className="rtas-howto-page__hero text-center">
        <p className="rtas-eyebrow">How to use</p>
        <h1 className="text-zinc-100">Studio Workflow Guide</h1>
        <p className="rtas-howto-page__lead">
          Enterprise-grade instructions for every video category — from secure authentication
          through render, preview, and licensed export. Built for international creators shipping
          music videos, ads, faith content, and narrative shorts at scale.
        </p>
        <div className="rtas-howto-page__actions">
          <ButtonLink href="/studio" variant="lavender">
            Open Studio <span aria-hidden>→</span>
          </ButtonLink>
          <ButtonLink href="#categories" variant="ghost">
            Jump to categories
          </ButtonLink>
        </div>
      </InnerPageSection>

      <InnerPageSection className="rtas-howto-section" aria-labelledby="howto-universal">
        <h2 id="howto-universal" className="text-zinc-100">
          Production launch sequence
        </h2>
        <p className="rtas-howto-section__intro">
          Five standardized steps every creator follows — regardless of category. Complete this
          sequence once, then dive into your specialized pipeline below.
        </p>
        <ol className="rtas-howto-timeline">
          {UNIVERSAL_STEPS.map((step, index) => (
            <li key={step.num} className="rtas-howto-timeline__item">
              <div className="rtas-howto-timeline__rail" aria-hidden>
                <span className="rtas-howto-timeline__node">{step.num}</span>
                {index < UNIVERSAL_STEPS.length - 1 ? (
                  <span className="rtas-howto-timeline__line" />
                ) : null}
              </div>
              <div className="rtas-howto-timeline__panel">
                <span
                  className={`rtas-howto-tag rtas-howto-tag--${step.tagVariant}`}
                >
                  {step.tag}
                </span>
                <h3 className="text-zinc-100">{step.title}</h3>
                <p>{step.detail}</p>
              </div>
            </li>
          ))}
        </ol>
      </InnerPageSection>

      <InnerPageSection className="rtas-howto-section" aria-labelledby="howto-flow">
        <h2 id="howto-flow" className="text-zinc-100">
          Studio configuration pipeline
        </h2>
        <p className="rtas-howto-section__intro">
          After authentication, configure inputs in sequence. Each stage unlocks the next — ensuring
          validated metadata before GPU render begins.
        </p>
        <div className="rtas-howto-flow">
          {STUDIO_FLOW.map((item, index) => (
            <div key={item.label} className="rtas-howto-flow__item">
              <span className="rtas-howto-flow__badge">{index + 1}</span>
              <div>
                <strong className="text-zinc-100">{item.label}</strong>
                <p>{item.options}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="rtas-howto-callout">
          <strong className="text-zinc-100">Identity Shielding tip:</strong> To appear on screen
          yourself, upload a clear front-facing photo and confirm consent with{" "}
          <code>YES</code> — this activates Authorized Identity Consistency across scenes.
        </div>
      </InnerPageSection>

      <InnerPageSection className="rtas-howto-jump" id="categories" aria-label="Category guides">
        <h2 className="text-zinc-100">Category production guides</h2>
        <ul className="rtas-howto-jump__list">
          {CATEGORY_GUIDES.map((guide) => (
            <li key={guide.id}>
              <a href={`#guide-${guide.id}`}>{guide.title}</a>
            </li>
          ))}
        </ul>
      </InnerPageSection>

      {CATEGORY_GUIDES.map((guide) => (
        <InnerPageSection
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
              <h2 id={`guide-title-${guide.id}`} className="text-zinc-100">
                {guide.title}
              </h2>
              <ul className="rtas-howto-value-tags" aria-label="Product capabilities">
                {guide.valueTags.map((tag) => (
                  <li key={tag} className="rtas-howto-tag rtas-howto-tag--gold">
                    {tag}
                  </li>
                ))}
              </ul>
              <p>{guide.summary}</p>

              <h3 className="text-zinc-100">Best for</h3>
              <ul className="rtas-howto-tags">
                {guide.bestFor.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>

              <div className="rtas-howto-reco">
                <h3 className="text-zinc-100">Recommended settings</h3>
                <dl>
                  <div>
                    <dt className="text-zinc-100">Mode</dt>
                    <dd>{guide.recommended.mode}</dd>
                  </div>
                  <div>
                    <dt className="text-zinc-100">Visual style</dt>
                    <dd>{guide.recommended.visualStyle}</dd>
                  </div>
                  <div>
                    <dt className="text-zinc-100">Length</dt>
                    <dd>{guide.recommended.length}</dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>

          <div className="rtas-howto-category__steps">
            <h3 className="text-zinc-100">Production checklist</h3>
            <ol className="rtas-howto-mini-steps">
              {guide.steps.map((step, index) => (
                <li key={step.title}>
                  <span className="rtas-howto-mini-steps__num">{index + 1}</span>
                  <div>
                    <strong className="text-zinc-100">{step.title}</strong>
                    <p>{step.detail}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>

          <div className="rtas-howto-tips">
            <h3 className="text-zinc-100">Tips</h3>
            <ul>
              {guide.tips.map((tip) => (
                <li key={tip}>{tip}</li>
              ))}
            </ul>
          </div>

          <ButtonLink href="/studio" variant="lavender" className="rtas-howto-category__cta">
            Create in Studio →
          </ButtonLink>
        </InnerPageSection>
      ))}

      <InnerPageSection className="rtas-howto-page__footer text-center">
        <h2 className="text-zinc-100">Need help?</h2>
        <p>
          Use live chat in the bottom-right corner or email{" "}
          <a href="mailto:support@rtasdigital.com">support@rtasdigital.com</a>.
        </p>
        <div className="rtas-howto-page__actions">
          <ButtonLink href="/pricing" variant="ghost">
            View pricing and credits
          </ButtonLink>
          <ButtonLink href="/studio" variant="lavender">
            Start creating
          </ButtonLink>
        </div>
      </InnerPageSection>
    </InnerPageContainer>
  );
}

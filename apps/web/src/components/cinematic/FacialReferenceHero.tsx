"use client";

import { useEffect, useState } from "react";
import type { FileFieldValue } from "@/lib/studio-form";

type Props = {
  faceFile: FileFieldValue | null;
  visible: boolean;
};

const BEST_PRACTICES = [
  "Use a sharp, front-facing portrait with even light",
  "Keep the face centered — chin to forehead visible",
  "Avoid sunglasses, masks, heavy makeup filters, or group shots",
];

export function FacialReferenceHero({ faceFile, visible }: Props) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!faceFile?.file) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(faceFile.file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [faceFile?.file, faceFile?.name]);

  if (!visible) return null;

  const hasReference = Boolean(previewUrl);

  return (
    <div className="shashka-face-hero-block">
      <div className="shashka-face-hero" aria-label="Facial reference lock">
        <div className="shashka-face-hero__halo" aria-hidden />
        <div className="shashka-face-hero__ring" aria-hidden />
        {previewUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={previewUrl}
            alt="Face reference for identity lock"
            className="shashka-face-hero__photo"
          />
        ) : (
          <div className="shashka-face-hero__placeholder">
            <span>Your face</span>
            <small>Upload to activate lock</small>
          </div>
        )}
        <span className="shashka-face-hero__tag">Identity Lock™</span>
      </div>

      {hasReference ? (
        <p className="shashka-face-hero__warn" role="status">
          Preview only — confirm this is the likeness you want locked for the full
          render. Re-upload if the crop, angle, or lighting looks off.
        </p>
      ) : (
        <p className="shashka-face-hero__warn shashka-face-hero__warn--pending" role="status">
          No reference yet. Identity lock needs a clear face photo before generate.
        </p>
      )}

      <ul className="shashka-face-hero__tips" aria-label="Face reference best practices">
        {BEST_PRACTICES.map((tip) => (
          <li key={tip}>{tip}</li>
        ))}
      </ul>
    </div>
  );
}

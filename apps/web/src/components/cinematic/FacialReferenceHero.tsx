"use client";

import { useEffect, useState } from "react";
import type { FileFieldValue } from "@/lib/studio-form";

type Props = {
  faceFile: FileFieldValue | null;
  visible: boolean;
};

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

  return (
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
  );
}

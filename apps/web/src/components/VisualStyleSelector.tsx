"use client";

import type { VisualStyle } from "@rtas/shared";
import { FacialConsistencyShield } from "@/components/cinematic/FacialConsistencyShield";

const STYLES: { id: VisualStyle; label: string }[] = [
  { id: "real", label: "Identity Preservation" },
  { id: "avatar", label: "Avatar" },
  { id: "cartoon", label: "Cartoon" },
];

type Props = {
  value: VisualStyle | null;
  onChange: (style: VisualStyle) => void;
  disabled?: boolean;
  compact?: boolean;
};

export function VisualStyleSelector({
  value,
  onChange,
  disabled = false,
  compact = false,
}: Props) {
  return (
    <div className={`visual-style-block${compact ? " visual-style-block--compact" : ""}`}>
      <p className="section-label">Visual style</p>
      <div className="chip-row">
        {STYLES.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            className={`chip ${value === id ? "active" : ""}`}
            onClick={() => onChange(id)}
            disabled={disabled}
            aria-pressed={value === id}
          >
            {label}
          </button>
        ))}
      </div>
      {value === "real" ? <FacialConsistencyShield /> : null}
    </div>
  );
}

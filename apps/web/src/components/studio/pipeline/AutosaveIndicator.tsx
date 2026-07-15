"use client";

type Props = {
  savedAt: string | null;
  saving?: boolean;
};

export function AutosaveIndicator({ savedAt, saving = false }: Props) {
  if (saving) {
    return (
      <span className="studio-autosave studio-autosave--saving" aria-live="polite">
        <span className="studio-autosave__dot" aria-hidden />
        Saving draft…
      </span>
    );
  }
  if (!savedAt) return null;

  return (
    <span
      className="studio-autosave"
      aria-live="polite"
      title="Draft autosaved on this device"
    >
      <span className="studio-autosave__check" aria-hidden>
        ✓
      </span>
      Draft saved{" "}
      {new Date(savedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
    </span>
  );
}

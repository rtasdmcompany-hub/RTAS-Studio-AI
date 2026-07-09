"use client";

type Props = {
  className?: string;
};

const SHORTCUTS = [
  { keys: "⌘↵", label: "Generate" },
  { keys: "Esc", label: "Cancel wait" },
  { keys: "⌘⇧R", label: "Retry" },
  { keys: "⌘.", label: "Create / Preview" },
  { keys: "⌘S", label: "Save draft" },
];

export function StudioShortcutsHint({ className = "" }: Props) {
  return (
    <div className={`studio-shortcuts-hint ${className}`.trim()} aria-label="Keyboard shortcuts">
      {SHORTCUTS.map((s) => (
        <span key={s.keys} className="studio-shortcuts-hint__item">
          <kbd>{s.keys}</kbd>
          <span>{s.label}</span>
        </span>
      ))}
    </div>
  );
}

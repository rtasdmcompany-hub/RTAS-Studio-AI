"use client";

export type StudioScreen = "create" | "preview";

type Props = {
  screen: StudioScreen;
  onScreenChange: (screen: StudioScreen) => void;
  /** Block returning to create while a render is in flight */
  createLocked?: boolean;
};

/** Fixed side rail — switch between full-screen Create and Preview views */
export function StudioScreenRail({
  screen,
  onScreenChange,
  createLocked = false,
}: Props) {
  return (
    <nav className="studio-screen-rail" aria-label="Studio screens">
      <button
        type="button"
        className={`studio-screen-rail__btn${
          screen === "create" ? " studio-screen-rail__btn--active" : ""
        }`}
        onClick={() => onScreenChange("create")}
        disabled={createLocked}
        aria-current={screen === "create" ? "page" : undefined}
        title={createLocked ? "Wait for render to finish" : "Create screen"}
      >
        <span className="studio-screen-rail__chev" aria-hidden>
          ↑
        </span>
        <span className="studio-screen-rail__label">Create</span>
      </button>
      <span className="studio-screen-rail__divider" aria-hidden />
      <button
        type="button"
        className={`studio-screen-rail__btn${
          screen === "preview" ? " studio-screen-rail__btn--active" : ""
        }`}
        onClick={() => onScreenChange("preview")}
        aria-current={screen === "preview" ? "page" : undefined}
        title="Preview screen"
      >
        <span className="studio-screen-rail__chev" aria-hidden>
          ↓
        </span>
        <span className="studio-screen-rail__label">Preview</span>
      </button>
    </nav>
  );
}

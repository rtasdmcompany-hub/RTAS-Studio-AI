"use client";

/** Fast-forward walkthrough — every box filled (title, mode, uploads, face, etc.). */
export function ShowcaseInputDemo() {
  return (
    <div className="showcase-input-demo" aria-label="How to use RTAS Studio demo">
      <div className="showcase-input-demo__top">
        <span className="showcase-input-demo__step-label">Step 1–4 · Fill the form</span>
        <span className="showcase-ff-badge">⏩ Demo fast-forward</span>
      </div>

      <div className="showcase-input-demo__viewport">
        <div className="showcase-input-demo__scroll showcase-anim-fast-scroll">
          <div className="showcase-step showcase-step--1">
            <span className="showcase-input-demo__section">Video Title</span>
            <div className="showcase-input-demo__field">
              <span className="showcase-input-demo__value showcase-anim-type-full">
                meri kahani
              </span>
            </div>
          </div>

          <div className="showcase-step showcase-step--2">
            <span className="showcase-input-demo__section">Mode</span>
            <div className="showcase-input-demo__chips">
              <span className="showcase-input-demo__chip">Prompt</span>
              <span className="showcase-input-demo__chip active">Image → Video</span>
            </div>
          </div>

          <div className="showcase-step showcase-step--3">
            <span className="showcase-input-demo__section">Category</span>
            <div className="showcase-input-demo__chips">
              <span className="showcase-input-demo__chip active">Song</span>
              <span className="showcase-input-demo__chip">Religious</span>
              <span className="showcase-input-demo__chip">Story</span>
            </div>
          </div>

          <div className="showcase-step showcase-step--4">
            <span className="showcase-input-demo__section">Visual Style</span>
            <div className="showcase-input-demo__chips">
              <span className="showcase-input-demo__chip active">Real face</span>
              <span className="showcase-input-demo__chip">Avatar</span>
            </div>
          </div>

          <div className="showcase-step showcase-step--5">
            <span className="showcase-input-demo__section">Lyrics</span>
            <div className="showcase-input-demo__field showcase-input-demo__field--multi">
              <span className="showcase-input-demo__value showcase-anim-lyrics">
                Suno meri kahani… emotional rap &amp; harmonium
              </span>
            </div>
          </div>

          <div className="showcase-step showcase-step--6">
            <span className="showcase-input-demo__section">Music Style</span>
            <div className="showcase-input-demo__field">
              <span className="showcase-input-demo__value showcase-anim-style">
                Trap beat · deep voice · cinematic
              </span>
            </div>
          </div>

          <div className="showcase-step showcase-step--7">
            <span className="showcase-input-demo__section">Audio track</span>
            <div className="showcase-input-demo__upload showcase-input-demo__upload--done">
              <span className="showcase-input-demo__upload-icon">🎵</span>
              <span>Suno Meri Kahani.mp3</span>
              <span className="showcase-input-demo__check">✓</span>
            </div>
          </div>

          <div className="showcase-step showcase-step--8">
            <span className="showcase-input-demo__section">Cover / reference image</span>
            <div className="showcase-input-demo__upload showcase-input-demo__upload--done">
              <span className="showcase-input-demo__upload-icon">🖼</span>
              <span>cover-art.jpeg</span>
              <span className="showcase-input-demo__check">✓</span>
            </div>
          </div>

          <div className="showcase-step showcase-step--9">
            <span className="showcase-input-demo__section">Source image (Image → Video)</span>
            <div className="showcase-input-demo__upload showcase-input-demo__upload--done">
              <span className="showcase-input-demo__upload-icon">📷</span>
              <span>starting-frame.jfif</span>
              <span className="showcase-input-demo__check">✓</span>
            </div>
          </div>

          <div className="showcase-step showcase-step--10">
            <span className="showcase-input-demo__section">Face photo (Identity Lock)</span>
            <div className="showcase-input-demo__upload showcase-input-demo__upload--done">
              <span className="showcase-input-demo__upload-icon">👤</span>
              <span>face-reference.jpeg</span>
              <span className="showcase-input-demo__check">✓</span>
            </div>
          </div>

          <div className="showcase-step showcase-step--11">
            <span className="showcase-input-demo__section">Face consent</span>
            <div className="showcase-input-demo__field">
              <span className="showcase-input-demo__value showcase-anim-consent">YES</span>
            </div>
          </div>

          <div className="showcase-step showcase-step--12">
            <span className="showcase-input-demo__section">Direction (Prompt)</span>
            <div className="showcase-input-demo__field showcase-input-demo__field--multi">
              <span className="showcase-input-demo__value showcase-anim-direction">
                5 min emotional cinematic music video…
              </span>
            </div>
          </div>

          <div className="showcase-step showcase-step--13">
            <span className="showcase-input-demo__section">Duration</span>
            <div className="showcase-input-demo__field">
              <span className="showcase-input-demo__value">30 seconds</span>
            </div>
          </div>
        </div>
      </div>

      <div className="showcase-input-demo__footer">
        <button type="button" className="showcase-input-demo__btn showcase-anim-generate-fast">
          Generate video
        </button>
        <div className="showcase-input-demo__progress">
          <div className="showcase-input-demo__progress-fill showcase-anim-progress-fast" />
        </div>
      </div>
    </div>
  );
}

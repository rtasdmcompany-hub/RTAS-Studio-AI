"use client";

type Props = {
  message: string;
  title?: string;
  hint?: string | null;
  onDismiss?: () => void;
};

export function BackendConnectionNotice({
  message,
  title = "API connection issue",
  hint,
  onDismiss,
}: Props) {
  const defaultHint =
    "Start the server: cd apps/backend && .venv\\Scripts\\python.exe -m uvicorn main:app --reload --port 8000";

  return (
    <div className="backend-notice" role="alert">
      <div className="backend-notice-icon" aria-hidden>
        ⚠
      </div>
      <div className="backend-notice-body">
        <p className="backend-notice-title">{title}</p>
        <p className="backend-notice-text">{message}</p>
        {hint !== null && (
          <p className="backend-notice-hint">
            {hint ?? defaultHint}
          </p>
        )}
      </div>
      {onDismiss && (
        <button
          type="button"
          className="backend-notice-dismiss"
          onClick={onDismiss}
          aria-label="Dismiss"
        >
          ×
        </button>
      )}
    </div>
  );
}

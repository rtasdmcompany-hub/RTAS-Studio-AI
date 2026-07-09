"use client";

import { Alert } from "@rtas/ui";

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
    <Alert
      variant="warning"
      legacyBackend
      title={title}
      message={message}
      hint={hint !== null ? (hint ?? defaultHint) : undefined}
      onDismiss={onDismiss}
    />
  );
}

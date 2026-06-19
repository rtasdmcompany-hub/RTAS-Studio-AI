"use client";

import type { FileFieldValue } from "@/lib/studio-form";

type Props = {
  id: string;
  label: string;
  accept?: string;
  helpText?: string;
  value: FileFieldValue | null;
  onChange: (value: FileFieldValue | null) => void;
  hasError?: boolean;
  errorMessage?: string;
  disabled?: boolean;
};

export function FileUploadField({
  id,
  label,
  accept,
  helpText,
  value,
  onChange,
  hasError = false,
  errorMessage,
  disabled = false,
}: Props) {
  return (
    <div
      className={`file-upload file-upload--${id}${hasError ? " file-upload--error" : ""}`}
    >
      <label htmlFor={id} className="file-upload-label">
        {label}
      </label>
      <div className="file-upload-row">
        <input
          id={id}
          type="file"
          accept={accept}
          className="file-upload-input"
          disabled={disabled}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (!file) {
              onChange(null);
              return;
            }
            onChange({
              file,
              name: file.name,
              mimeType: file.type,
              size: file.size,
            });
          }}
        />
        {value ? (
          <span className="file-upload-name" title={value.name}>
            {value.name}
            <button
              type="button"
              className="file-upload-clear"
              disabled={disabled}
              onClick={() => onChange(null)}
              aria-label="Remove file"
            >
              ×
            </button>
          </span>
        ) : (
          <span className="file-upload-placeholder">Choose file…</span>
        )}
      </div>
      {hasError && errorMessage ? (
        <p className="field-error" role="alert">
          {errorMessage}
        </p>
      ) : null}
      {helpText && !hasError ? <p className="help">{helpText}</p> : null}
    </div>
  );
}

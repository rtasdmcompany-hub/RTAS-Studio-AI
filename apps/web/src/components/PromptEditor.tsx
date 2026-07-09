"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import { FormFieldRestoreHint } from "./FormFieldRestoreHint";

type Props = {
  id: string;
  label: string;
  value: string;
  placeholder?: string;
  helpText?: string;
  hasError?: boolean;
  errorMessage?: string;
  disabled?: boolean;
  rows?: number;
  maxLength?: number;
  onChange: (value: string) => void;
  /** Soft guidance chips shown above the editor */
  suggestions?: string[];
};

const DEFAULT_SUGGESTIONS = [
  "cinematic lighting",
  "slow camera push-in",
  "shallow depth of field",
  "golden hour",
  "identity lock",
];

export function PromptEditor({
  id,
  label,
  value,
  placeholder,
  helpText,
  hasError = false,
  errorMessage,
  disabled = false,
  rows = 5,
  maxLength = 4000,
  onChange,
  suggestions = DEFAULT_SUGGESTIONS,
}: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const reactId = useId();
  const [focused, setFocused] = useState(false);
  const count = value.length;
  const nearLimit = count > maxLength * 0.9;

  const resize = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 320)}px`;
  }, []);

  useEffect(() => {
    resize();
  }, [value, resize]);

  const insertSuggestion = (chip: string) => {
    if (disabled) return;
    const el = textareaRef.current;
    const next =
      value.trim().length === 0
        ? chip
        : value.endsWith(" ") || value.endsWith(",")
          ? `${value}${chip}`
          : `${value.trim()}, ${chip}`;
    onChange(next.slice(0, maxLength));
    requestAnimationFrame(() => {
      el?.focus();
      const pos = Math.min(next.length, maxLength);
      el?.setSelectionRange(pos, pos);
    });
  };

  return (
    <div
      className={[
        "prompt-editor",
        `prompt-editor--${id}`,
        hasError ? "prompt-editor--error" : "",
        focused ? "prompt-editor--focused" : "",
        disabled ? "prompt-editor--disabled" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="prompt-editor__header">
        <label htmlFor={reactId} className="prompt-editor__label">
          {label}
        </label>
        <span
          className={`prompt-editor__count${nearLimit ? " prompt-editor__count--warn" : ""}`}
          aria-live="polite"
        >
          {count.toLocaleString()}
          {maxLength ? ` / ${maxLength.toLocaleString()}` : ""}
        </span>
      </div>

      {suggestions.length > 0 ? (
        <div className="prompt-editor__chips" role="list" aria-label="Prompt suggestions">
          {suggestions.map((chip) => (
            <button
              key={chip}
              type="button"
              role="listitem"
              className="prompt-editor__chip"
              disabled={disabled}
              onClick={() => insertSuggestion(chip)}
            >
              {chip}
            </button>
          ))}
        </div>
      ) : null}

      <FormFieldRestoreHint
        fieldId={id}
        currentValue={value}
        fieldLabel={label}
        onApplyField={onChange}
      >
        <textarea
          ref={textareaRef}
          id={reactId}
          className="prompt-editor__textarea"
          placeholder={placeholder}
          value={value}
          rows={rows}
          maxLength={maxLength}
          disabled={disabled}
          aria-invalid={hasError}
          aria-describedby={helpText || hasError ? `${reactId}-hint` : undefined}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
        />
      </FormFieldRestoreHint>

      <div className="prompt-editor__footer" id={`${reactId}-hint`}>
        {hasError && errorMessage ? (
          <p className="field-error" role="alert">
            {errorMessage}
          </p>
        ) : helpText ? (
          <p className="help">{helpText}</p>
        ) : (
          <p className="prompt-editor__tip">
            Tip: describe subject, camera, lighting, and mood. ⌘↵ to generate.
          </p>
        )}
      </div>
    </div>
  );
}

"use client";

import type { ReactElement } from "react";
import {
  DURATION_FIELD,
  getVisibleFields,
  type CategoryField,
  type GenerationMode,
  type VideoCategory,
  type VisualStyle,
} from "@rtas/shared";
import type { FileFieldValue, StudioFormState } from "@/lib/studio-form";
import {
  CreateFormCostNotice,
  parseDurationSeconds,
} from "@/components/create-form";
import { FileUploadField } from "./FileUploadField";
import { FormFieldRestoreHint } from "./FormFieldRestoreHint";

type Props = {
  category: VideoCategory;
  mode: GenerationMode;
  visualStyle: VisualStyle;
  form: StudioFormState;
  fieldErrors: Record<string, string>;
  disabled?: boolean;
  onTextChange: (id: string, value: string) => void;
  onFileChange: (id: string, value: FileFieldValue | null) => void;
};

function renderTextControl(
  f: CategoryField,
  form: StudioFormState,
  hasError: boolean,
  disabled: boolean,
  onTextChange: Props["onTextChange"],
  maxDurationSeconds?: number
) {
  const label = f.shortLabel || f.label;
  const value = form.text[f.id] ?? "";
  const errorClass = hasError ? " field-input--error" : "";

  const wrap = (control: ReactElement) => (
    <FormFieldRestoreHint
      fieldId={f.id}
      currentValue={value}
      fieldLabel={label}
      onApplyField={(next) => onTextChange(f.id, next)}
    >
      {control}
    </FormFieldRestoreHint>
  );

  if (f.type === "textarea") {
    return wrap(
      <textarea
        id={f.id}
        className={errorClass.trim() || undefined}
        placeholder={f.placeholder}
        value={value}
        onChange={(e) => onTextChange(f.id, e.target.value)}
        disabled={disabled}
        aria-invalid={hasError}
      />
    );
  }

  if (f.type === "select") {
    const options =
      f.id === "duration" && maxDurationSeconds !== undefined
        ? f.options?.filter((o) => Number.parseInt(o.value, 10) <= maxDurationSeconds)
        : f.options;
    return wrap(
      <select
        id={f.id}
        className={errorClass.trim() || undefined}
        value={value}
        onChange={(e) => onTextChange(f.id, e.target.value)}
        disabled={disabled}
        aria-invalid={hasError}
      >
        <option value="">Select…</option>
        {options?.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    );
  }

  return wrap(
    <input
      id={f.id}
      type="text"
      className={errorClass.trim() || undefined}
      placeholder={f.placeholder}
      value={value}
      onChange={(e) => onTextChange(f.id, e.target.value)}
      disabled={disabled}
      aria-invalid={hasError}
    />
  );
}

function renderField(
  f: CategoryField,
  form: StudioFormState,
  fieldErrors: Record<string, string>,
  disabled: boolean,
  onTextChange: Props["onTextChange"],
  onFileChange: Props["onFileChange"],
  maxDurationSeconds?: number
) {
  const label = f.shortLabel || f.label;
  const errorMessage = fieldErrors[f.id];
  const hasError = Boolean(errorMessage);

  if (f.type === "file") {
    return (
      <FileUploadField
        key={f.id}
        id={f.id}
        label={label}
        accept={f.accept}
        helpText={f.helpText}
        value={form.files[f.id] ?? null}
        onChange={(v) => onFileChange(f.id, v)}
        disabled={disabled}
        hasError={hasError}
        errorMessage={errorMessage}
      />
    );
  }

  return (
    <div
      key={f.id}
      className={`field field--${f.id}${hasError ? " field--error" : ""}`}
    >
      <label htmlFor={f.id}>{label}</label>
      {renderTextControl(f, form, hasError, disabled, onTextChange, maxDurationSeconds)}
      {hasError ? (
        <p className="field-error" role="alert">
          {errorMessage}
        </p>
      ) : (
        f.helpText && <p className="help">{f.helpText}</p>
      )}
    </div>
  );
}

type SingleFieldProps = {
  field: CategoryField;
  form: StudioFormState;
  fieldErrors: Record<string, string>;
  disabled?: boolean;
  maxDurationSeconds?: number;
  onTextChange: (id: string, value: string) => void;
  onFileChange: (id: string, value: FileFieldValue | null) => void;
};

/** One category field — used by the step-by-step wizard. */
export function CategoryWizardField({
  field,
  form,
  fieldErrors,
  disabled = false,
  maxDurationSeconds,
  onTextChange,
  onFileChange,
}: SingleFieldProps) {
  return renderField(
    field,
    form,
    fieldErrors,
    disabled,
    onTextChange,
    onFileChange,
    maxDurationSeconds
  );
}

type GroupProps = {
  fields: CategoryField[];
  form: StudioFormState;
  fieldErrors: Record<string, string>;
  disabled?: boolean;
  maxDurationSeconds?: number;
  onTextChange: (id: string, value: string) => void;
  onFileChange: (id: string, value: FileFieldValue | null) => void;
};

/** Multiple fields on one wizard page. */
export function CategoryWizardGroup({
  fields,
  form,
  fieldErrors,
  disabled = false,
  maxDurationSeconds,
  onTextChange,
  onFileChange,
}: GroupProps) {
  return (
    <div className="category-wizard-group">
      {fields.map((field) =>
        renderField(
          field,
          form,
          fieldErrors,
          disabled,
          onTextChange,
          onFileChange,
          maxDurationSeconds
        )
      )}
    </div>
  );
}

export function CategoryFieldsSection({
  category,
  mode,
  visualStyle,
  form,
  fieldErrors,
  disabled = false,
  onTextChange,
  onFileChange,
}: Props) {
  const modeAndCategoryFields = getVisibleFields(category, mode, visualStyle);

  return (
    <div
      className="category-fields"
      key={`${category}-${mode}-${visualStyle}`}
      role="region"
      aria-label={`${category} fields`}
    >
      <p className="section-label">Video length</p>
      {renderField(DURATION_FIELD, form, fieldErrors, disabled, onTextChange, onFileChange)}
      <CreateFormCostNotice
        durationSeconds={parseDurationSeconds(form.text.duration)}
        category={category}
        visualStyle={visualStyle}
      />

      <p className="section-label">
        {mode === "image" ? "Image mode" : "Visual scene"}
      </p>
      {modeAndCategoryFields
        .filter((f) => f.id === "mainPrompt" || f.id === "sourceImage")
        .map((f) => renderField(f, form, fieldErrors, disabled, onTextChange, onFileChange))}

      <p className="section-label">Category details</p>
      {modeAndCategoryFields
        .filter((f) => f.id !== "mainPrompt" && f.id !== "sourceImage")
        .map((f) => renderField(f, form, fieldErrors, disabled, onTextChange, onFileChange))}
    </div>
  );
}

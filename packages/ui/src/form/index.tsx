import type {
  HTMLAttributes,
  InputHTMLAttributes,
  LabelHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";
import { cn } from "../lib/cn";

export type FieldProps = {
  id?: string;
  label?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  children: ReactNode;
  className?: string;
};

export function Field({
  id,
  label,
  hint,
  error,
  required,
  children,
  className,
}: FieldProps) {
  return (
    <div className={cn("rtas-ui-field field", className)}>
      {label ? (
        <Label htmlFor={id} required={required}>
          {label}
        </Label>
      ) : null}
      {children}
      {error ? <FieldError>{error}</FieldError> : null}
      {!error && hint ? <p className="rtas-ui-field-hint help">{hint}</p> : null}
    </div>
  );
}

export type LabelProps = LabelHTMLAttributes<HTMLLabelElement> & {
  required?: boolean;
};

export function Label({ required, className, children, ...props }: LabelProps) {
  return (
    <label {...props} className={cn("rtas-ui-label", className)}>
      {children}
      {required ? (
        <span className="text-ds-danger-soft" aria-hidden>
          {" "}
          *
        </span>
      ) : null}
    </label>
  );
}

export type FieldErrorProps = HTMLAttributes<HTMLParagraphElement>;

export function FieldError({ className, children, ...props }: FieldErrorProps) {
  return (
    <p {...props} className={cn("rtas-ui-field-error field-error", className)} role="alert">
      {children}
    </p>
  );
}

export type InputProps = InputHTMLAttributes<HTMLInputElement>;

export function Input({ className, ...props }: InputProps) {
  return (
    <input
      {...props}
      className={cn("rtas-ui-input rtas-ui-focus-ring rtas-ui-skip-focus", className)}
    />
  );
}

export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>;

export function Textarea({ className, ...props }: TextareaProps) {
  return (
    <textarea
      {...props}
      className={cn("rtas-ui-textarea rtas-ui-focus-ring rtas-ui-skip-focus", className)}
    />
  );
}

export type SelectProps = SelectHTMLAttributes<HTMLSelectElement>;

export function Select({ className, children, ...props }: SelectProps) {
  return (
    <select
      {...props}
      className={cn("rtas-ui-select rtas-ui-focus-ring rtas-ui-skip-focus", className)}
    >
      {children}
    </select>
  );
}

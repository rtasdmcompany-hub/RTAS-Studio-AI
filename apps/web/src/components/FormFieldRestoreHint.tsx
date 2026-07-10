"use client";

import {
  cloneElement,
  useCallback,
  useEffect,
  useRef,
  useState,
  type FocusEvent,
  type MouseEvent,
  type ReactElement,
} from "react";
import { getFieldLastValue, truncatePreview } from "@/lib/studio-form-backup";

type FieldElementProps = {
  onFocus?: (event: FocusEvent<HTMLElement>) => void;
  onClick?: (event: MouseEvent<HTMLElement>) => void;
};

type Props = {
  fieldId: string;
  currentValue: string;
  fieldLabel: string;
  onApplyField: (value: string) => void;
  children: ReactElement<FieldElementProps>;
};

export function FormFieldRestoreHint({
  fieldId,
  currentValue,
  fieldLabel,
  onApplyField,
  children,
}: Props) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);

  const lastValue = getFieldLastValue(fieldId);
  const canSuggestField = Boolean(
    lastValue && lastValue.trim() !== currentValue.trim()
  );

  const openIfHelpful = useCallback(() => {
    if (canSuggestField) setOpen(true);
  }, [canSuggestField]);

  useEffect(() => {
    if (!open) return;
    const onDocMouseDown = (event: globalThis.MouseEvent) => {
      if (!wrapRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const onDocKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDocMouseDown);
    document.addEventListener("keydown", onDocKeyDown);
    return () => {
      document.removeEventListener("mousedown", onDocMouseDown);
      document.removeEventListener("keydown", onDocKeyDown);
    };
  }, [open]);

  const child = cloneElement(children, {
    onFocus: (event: FocusEvent<HTMLElement>) => {
      children.props.onFocus?.(event);
      openIfHelpful();
    },
    onClick: (event: MouseEvent<HTMLElement>) => {
      children.props.onClick?.(event);
      openIfHelpful();
    },
  });

  return (
    <div className="field-with-restore" ref={wrapRef}>
      {child}
      {open && canSuggestField && lastValue && (
        <div
          className="form-restore-popup"
          role="listbox"
          aria-label={`${fieldLabel} suggestions`}
        >
          <button
            type="button"
            className="form-restore-option"
            role="option"
            aria-selected="false"
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => {
              onApplyField(lastValue);
              setOpen(false);
            }}
          >
            <span className="form-restore-option-label">Last filled value</span>
            <span className="form-restore-option-preview">
              {truncatePreview(lastValue)}
            </span>
          </button>
        </div>
      )}
    </div>
  );
}

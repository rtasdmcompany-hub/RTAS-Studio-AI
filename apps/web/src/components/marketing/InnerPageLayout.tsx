import type { ElementType, HTMLAttributes, ReactNode } from "react";

/** Shared horizontal rhythm for marketing inner routes. */
export const INNER_PAGE_CONTAINER_CLASS =
  "inner-page-container max-w-6xl mx-auto px-4 pt-0 pb-10 flex flex-col gap-6";

/** Premium glass section shell for inner routes — aligned to design tokens. */
export const INNER_PAGE_SECTION_CLASS =
  "inner-page-section backdrop-blur-ds-xl bg-ds-surface-glass border border-ds-border rounded-2xl p-6 md:p-8 shadow-ds-2xl text-ds-text";

type ContainerProps = {
  children: ReactNode;
  className?: string;
};

export function InnerPageContainer({ children, className = "" }: ContainerProps) {
  return (
    <div className={`${INNER_PAGE_CONTAINER_CLASS} ${className}`.trim()}>
      {children}
    </div>
  );
}

type SectionProps = HTMLAttributes<HTMLElement> & {
  children: ReactNode;
  className?: string;
  as?: ElementType;
};

export function InnerPageSection({
  children,
  className = "",
  as: Tag = "section",
  ...props
}: SectionProps) {
  return (
    <Tag className={`${INNER_PAGE_SECTION_CLASS} ${className}`.trim()} {...props}>
      {children}
    </Tag>
  );
}

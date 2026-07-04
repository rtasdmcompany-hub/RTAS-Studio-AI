import type { ElementType, HTMLAttributes, ReactNode } from "react";

/** Shared horizontal rhythm for marketing inner routes. */
export const INNER_PAGE_CONTAINER_CLASS =
  "inner-page-container max-w-6xl mx-auto px-4 pt-24 pb-12 flex flex-col gap-8";

/** Premium glass section shell for inner routes. */
export const INNER_PAGE_SECTION_CLASS =
  "inner-page-section backdrop-blur-xl bg-white/[0.02] border border-white/[0.05] rounded-2xl p-6 md:p-10 shadow-2xl shadow-black/40 text-zinc-400";

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

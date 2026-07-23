import Link from "next/link";
import {
  ENTERPRISE_TRUST_ITEMS,
  ENTERPRISE_TRUST_MATURITY_LABELS,
  type EnterpriseTrustItem,
} from "@/lib/enterprise/trust";

type Props = {
  /** Limit items; default all */
  limit?: number;
  /** Filter by maturity */
  maturity?: EnterpriseTrustItem["maturity"][];
  className?: string;
  heading?: string;
  showLinks?: boolean;
};

const MATURITY_CLASS: Record<EnterpriseTrustItem["maturity"], string> = {
  shipped: "border-emerald-500/40 text-emerald-300",
  posture: "border-sky-500/40 text-sky-200",
  roadmap: "border-amber-500/40 text-amber-200",
};

/**
 * Reusable enterprise trust / security posture UI.
 * Does not claim SOC 2 / ISO certification.
 */
export function EnterpriseTrustPanel({
  limit,
  maturity,
  className = "",
  heading = "Security & trust posture",
  showLinks = true,
}: Props) {
  let items = ENTERPRISE_TRUST_ITEMS;
  if (maturity?.length) {
    items = items.filter((i) => maturity.includes(i.maturity));
  }
  if (typeof limit === "number") {
    items = items.slice(0, Math.max(1, limit));
  }

  return (
    <section
      className={`space-y-4 ${className}`.trim()}
      aria-labelledby="enterprise-trust-heading"
    >
      <div className="text-center md:text-left">
        <h2 id="enterprise-trust-heading" className="text-xl text-zinc-100">
          {heading}
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-ds-text-muted">
          Controls that ship today vs compliance posture vs roadmap. “Compliance-ready” means
          questionnaire and policy readiness — not a certification badge.
        </p>
      </div>
      <ul className="grid gap-3 md:grid-cols-2">
        {items.map((item) => (
          <li
            key={item.id}
            className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-base text-zinc-100">{item.title}</h3>
              <span
                className={`rounded-md border px-2 py-0.5 text-xs ${MATURITY_CLASS[item.maturity]}`}
              >
                {ENTERPRISE_TRUST_MATURITY_LABELS[item.maturity]}
              </span>
            </div>
            <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
          </li>
        ))}
      </ul>
      {showLinks ? (
        <p className="text-sm text-ds-text-muted">
          <Link href="/trust-safety" className="text-ds-accent-lavender hover:underline">
            Trust & Safety
          </Link>
          {" · "}
          <Link href="/privacy" className="text-ds-accent-lavender hover:underline">
            Privacy
          </Link>
          {" · "}
          <Link href="/ai-policy" className="text-ds-accent-lavender hover:underline">
            AI Policy
          </Link>
        </p>
      ) : null}
    </section>
  );
}

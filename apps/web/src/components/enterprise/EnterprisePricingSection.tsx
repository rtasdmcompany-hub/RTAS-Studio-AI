import Link from "next/link";
import { ButtonLink } from "@rtas/ui";
import { ENTERPRISE_COMMERCIAL_TIERS } from "@/lib/enterprise/pricing";

export function EnterprisePricingSection() {
  return (
    <section className="space-y-4" aria-labelledby="ent-commercial-pricing">
      <div className="inner-page-section text-center pb-2">
        <h2 id="ent-commercial-pricing" className="text-xl text-zinc-100">
          Enterprise pricing
        </h2>
        <p className="mx-auto mt-2 max-w-2xl text-sm text-ds-text-muted">
          Commercial naming: Tester · Creator · Business · Enterprise. Creator maps to published{" "}
          <strong className="font-medium text-zinc-200">Standard</strong>; Business maps to{" "}
          <strong className="font-medium text-zinc-200">Premium 4K</strong>. Enterprise has{" "}
          <strong className="font-medium text-zinc-200">no fixed public price</strong>.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {ENTERPRISE_COMMERCIAL_TIERS.map((tier) => (
          <article
            key={tier.id}
            className="inner-page-section inner-page-section--panel flex flex-col backdrop-blur-ds-xl border border-white/10 rounded-2xl p-5"
          >
            <p className="text-xs uppercase tracking-wide text-ds-text-muted">{tier.mapsTo}</p>
            <h3 className="mt-1 text-lg text-zinc-100">{tier.name}</h3>
            <p className="mt-3 text-2xl font-semibold text-zinc-50">{tier.priceLabel}</p>
            <p className="mt-1 text-sm text-ds-text-muted">{tier.priceDetail}</p>
            <p className="mt-2 text-sm text-ds-text-muted">{tier.creditsLabel}</p>
            <ul className="mt-4 flex-1 list-disc space-y-1 pl-5 text-sm text-ds-text-muted">
              {tier.highlights.map((h) => (
                <li key={h}>{h}</li>
              ))}
            </ul>
            <div className="mt-5 flex flex-col gap-2">
              <ButtonLink
                href={tier.cta.href}
                variant={tier.id === "enterprise" ? "lavender" : "ghost"}
              >
                {tier.cta.label}
              </ButtonLink>
              {tier.id === "enterprise" ? (
                <div className="flex flex-wrap gap-2 text-sm">
                  <Link
                    href="/demo"
                    className="text-ds-accent-lavender hover:underline"
                  >
                    Book Demo
                  </Link>
                  <span className="text-ds-text-muted" aria-hidden>
                    ·
                  </span>
                  <Link
                    href="/enterprise#contact"
                    className="text-ds-accent-lavender hover:underline"
                  >
                    Request Proposal
                  </Link>
                </div>
              ) : null}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

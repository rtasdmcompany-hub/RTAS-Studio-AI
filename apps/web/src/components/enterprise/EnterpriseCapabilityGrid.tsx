import {
  ENTERPRISE_CAPABILITIES,
  ENTERPRISE_CAPABILITY_STATUS_LABELS,
  type EnterpriseCapabilityStatus,
} from "@/lib/enterprise/capabilities";

const STATUS_CLASS: Record<EnterpriseCapabilityStatus, string> = {
  available: "border-emerald-500/40 text-emerald-300",
  roadmap: "border-amber-500/40 text-amber-200",
  contact: "border-ds-accent-lavender/40 text-ds-accent-lavender",
};

export function EnterpriseCapabilityGrid() {
  return (
    <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" aria-labelledby="ent-capabilities">
      <div className="inner-page-section md:col-span-2 lg:col-span-3 text-center pb-2">
        <h2 id="ent-capabilities" className="text-xl text-zinc-100">
          Enterprise capabilities
        </h2>
        <p className="mx-auto mt-2 max-w-2xl text-sm text-ds-text-muted">
          Honest availability labels — Available, Roadmap, or Contact for scoping. We do not claim a
          live private GPU fleet or unlimited credits.
        </p>
      </div>
      {ENTERPRISE_CAPABILITIES.map((cap) => (
        <article
          key={cap.id}
          className="inner-page-section inner-page-section--panel backdrop-blur-ds-xl border border-white/10 rounded-2xl p-5"
        >
          <div className="flex flex-wrap items-start justify-between gap-2">
            <h3 className="text-lg text-zinc-100">{cap.title}</h3>
            <span
              className={`rounded-md border px-2 py-0.5 text-xs ${STATUS_CLASS[cap.status]}`}
            >
              {ENTERPRISE_CAPABILITY_STATUS_LABELS[cap.status]}
            </span>
          </div>
          <p className="mt-2 text-sm text-ds-text-muted">{cap.description}</p>
        </article>
      ))}
    </section>
  );
}

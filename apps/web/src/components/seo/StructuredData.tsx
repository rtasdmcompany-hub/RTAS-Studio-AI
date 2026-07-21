type JsonLdValue = Record<string, unknown>;

type StructuredDataProps = {
  data: JsonLdValue | JsonLdValue[];
};

/** Renders Schema.org JSON-LD for crawlers that execute structured data. */
export function StructuredData({ data }: StructuredDataProps) {
  const graphs = Array.isArray(data) ? data : [data];

  if (graphs.length === 1) {
    return (
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(graphs[0]) }}
      />
    );
  }

  const stripped = graphs.map(({ "@context": _, ...rest }) => rest);
  const payload = { "@context": "https://schema.org", "@graph": stripped };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(payload) }}
    />
  );
}

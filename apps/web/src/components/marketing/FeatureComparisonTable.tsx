import {
  FEATURE_MATRIX,
  type PlanCell,
} from "@/lib/feature-comparison";

function cellLabel(value: PlanCell): string {
  if (value === "yes") return "Included";
  if (value === "no") return "Not included";
  if (value === "partial") return "Limited";
  return value;
}

function Cell({ value }: { value: PlanCell }) {
  const kind =
    value === "yes" ? "yes" : value === "no" ? "no" : value === "partial" ? "partial" : "text";

  return (
    <td className={`rtas-feature-matrix__cell rtas-feature-matrix__cell--${kind}`}>
      {kind === "yes" ? (
        <span aria-label="Included">✓</span>
      ) : kind === "no" ? (
        <span aria-label="Not included">—</span>
      ) : (
        <span>{cellLabel(value)}</span>
      )}
    </td>
  );
}

export function FeatureComparisonTable() {
  let lastCategory = "";

  return (
    <div className="rtas-feature-matrix-wrap">
      <table className="rtas-feature-matrix">
        <caption className="sr-only">
          Feature comparison across Creator Starter, Pro Studio, and Production Enterprise
        </caption>
        <thead>
          <tr>
            <th scope="col">Feature</th>
            <th scope="col">Starter</th>
            <th scope="col" className="rtas-feature-matrix__col--featured">
              Pro
            </th>
            <th scope="col">Enterprise</th>
          </tr>
        </thead>
        <tbody>
          {FEATURE_MATRIX.map((row) => {
            const showCategory = row.category !== lastCategory;
            lastCategory = row.category;
            return (
              <tr key={row.id}>
                <th scope="row">
                  {showCategory ? (
                    <span className="rtas-feature-matrix__category">{row.category}</span>
                  ) : null}
                  <span className="rtas-feature-matrix__feature">{row.feature}</span>
                </th>
                <Cell value={row.starter} />
                <Cell value={row.pro} />
                <Cell value={row.enterprise} />
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

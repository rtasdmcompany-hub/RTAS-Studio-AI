import { PRODUCT_NAME } from "@rtas/shared";
import { fetchAdminFundingSnapshot } from "@/lib/admin-api";

export default async function AdminHomePage() {
  const result = await fetchAdminFundingSnapshot();

  return (
    <main className="admin-shell">
      <header className="admin-header">
        <h1>{PRODUCT_NAME} Admin</h1>
        <p>Owner dashboard — Fal pool health, ledger, and backend controls.</p>
      </header>

      {result.error ? (
        <section className="admin-error" role="alert">
          <strong>Unable to load Fal funding status.</strong>
          <p className="admin-muted">{result.error}</p>
          <p className="admin-muted">
            Ensure <code>WEB_APP_URL</code> points at <code>@rtas/web</code> and{" "}
            <code>RTAS_ADMIN_SECRET</code> matches production.
          </p>
        </section>
      ) : (
        <>
          <section className="admin-card">
            <h2>Fal pool snapshot</h2>
            <dl className="admin-grid">
              <div className="admin-stat">
                <dt>Balance (USD)</dt>
                <dd>
                  {result.data?.snapshot.balanceUsd != null
                    ? `$${result.data.snapshot.balanceUsd.toFixed(2)}`
                    : "—"}
                </dd>
              </div>
              <div className="admin-stat">
                <dt>Required pool</dt>
                <dd>${result.data?.snapshot.requiredPoolUsd.toFixed(2) ?? "—"}</dd>
              </div>
              <div className="admin-stat">
                <dt>Active premium</dt>
                <dd>{result.data?.snapshot.activePremium ?? 0}</dd>
              </div>
              <div className="admin-stat">
                <dt>Active tester</dt>
                <dd>{result.data?.snapshot.activeTester ?? 0}</dd>
              </div>
              <div className="admin-stat">
                <dt>Shortfall</dt>
                <dd>${result.data?.snapshot.shortfallUsd.toFixed(2) ?? "0.00"}</dd>
              </div>
              <div className="admin-stat">
                <dt>Ledger entries</dt>
                <dd>{result.data?.ledger.totalEntries ?? 0}</dd>
              </div>
            </dl>
            {result.data?.snapshot.alertMessage ? (
              <p className="admin-alert">{result.data.snapshot.alertMessage}</p>
            ) : null}
            <div className="admin-actions">
              <a
                className="admin-btn admin-btn--primary"
                href={result.data?.falBillingUrl ?? "https://fal.ai/dashboard/billing"}
                target="_blank"
                rel="noreferrer"
              >
                Open Fal billing
              </a>
              <a className="admin-btn" href="/api/fal-funding/refresh">
                Refresh snapshot
              </a>
            </div>
          </section>

          <section className="admin-card">
            <h2>Connected services</h2>
            <p className="admin-muted">
              Web app: {process.env.WEB_APP_URL ?? "http://localhost:3000"}
            </p>
            <p className="admin-muted">
              FastAPI: {process.env.FASTAPI_URL ?? "http://localhost:8000"}
            </p>
            <div className="admin-actions">
              <a className="admin-btn" href={process.env.WEB_APP_URL ?? "http://localhost:3000"}>
                Open studio web
              </a>
            </div>
          </section>
        </>
      )}
    </main>
  );
}

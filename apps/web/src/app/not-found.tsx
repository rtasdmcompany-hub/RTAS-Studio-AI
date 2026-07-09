import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";

export const metadata = {
  title: `Page not found · ${PRODUCT_NAME}`,
};

export default function NotFound() {
  return (
    <div className="rtas-fullpage-state">
      <div className="rtas-fullpage-state__card" role="status">
        <span className="rtas-fullpage-state__code" aria-hidden>
          404
        </span>
        <h1 className="rtas-fullpage-state__title">This page took a wrong turn</h1>
        <p className="rtas-fullpage-state__desc">
          The page you&apos;re looking for doesn&apos;t exist or may have moved. Let&apos;s
          get you back to creating.
        </p>
        <div className="rtas-fullpage-state__actions">
          <ButtonLink href="/studio" variant="lavender">
            Open Studio <span aria-hidden>→</span>
          </ButtonLink>
          <ButtonLink href="/" variant="ghost">
            Back to home
          </ButtonLink>
        </div>
      </div>
    </div>
  );
}

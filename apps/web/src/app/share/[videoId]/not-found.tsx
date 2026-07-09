import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";
import { EmptyState } from "@rtas/ui";

export default function ShareNotFound() {
  return (
    <div className="share-page share-page--empty">
      <EmptyState
        className="share-page__empty-card"
        icon="🔗"
        title="Video not available"
        description="This link may have expired or the creator has not made this video public yet."
        action={
          <Link href="/studio" className="share-page__cta-btn rtas-ui-focus-ring">
            Create your own AI video with {PRODUCT_NAME} <span aria-hidden>→</span>
          </Link>
        }
      />
    </div>
  );
}

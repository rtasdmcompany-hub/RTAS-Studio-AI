import Link from "next/link";
import { PRODUCT_NAME } from "@rtas/shared";

export default function ShareNotFound() {
  return (
    <div className="share-page share-page--empty">
      <div className="share-page__empty-card">
        <h1>Video not available</h1>
        <p>
          This link may have expired or the creator has not made this video public yet.
        </p>
        <Link href="/" className="share-page__cta-btn">
          Create Your Own AI Video with {PRODUCT_NAME}
        </Link>
      </div>
    </div>
  );
}

import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { FeedbackClient } from "./FeedbackClient";

export const metadata: Metadata = {
  title: `Feedback · ${PRODUCT_NAME}`,
  description: `Send feedback, bug reports, and feature requests for ${PRODUCT_NAME}.`,
};

export default function FeedbackPage() {
  return <FeedbackClient />;
}

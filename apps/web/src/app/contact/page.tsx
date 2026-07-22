import { redirect } from "next/navigation";

/** Alias for typed URLs and external links → Help contact. */
export default function ContactAliasPage() {
  redirect("/help/contact");
}

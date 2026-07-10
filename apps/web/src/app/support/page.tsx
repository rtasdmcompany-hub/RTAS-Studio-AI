import { redirect } from "next/navigation";

/** Alias for support emails and external links → Help contact. */
export default function SupportAliasPage() {
  redirect("/help/contact");
}

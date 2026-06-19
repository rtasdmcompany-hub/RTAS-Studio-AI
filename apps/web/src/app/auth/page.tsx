import { redirect } from "next/navigation";

/** `/auth` has no UI — send visitors to the login screen. */
export default function AuthPage() {
  redirect("/auth/login");
}

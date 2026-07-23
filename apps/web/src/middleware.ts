import { getToken } from "next-auth/jwt";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { getNextAuthSecret } from "@/lib/env";

const PROTECTED_PREFIXES = [
  "/studio",
  "/profile",
  "/affiliate/dashboard",
  "/partners/dashboard",
  "/tickets",
  "/retention",
] as const;
const CANONICAL_HOST = "rtasstudio.com";

function isProtectedPath(pathname: string): boolean {
  return PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
  );
}

export async function middleware(request: NextRequest) {
  const host = request.headers.get("host") ?? "";

  if (
    host === `www.${CANONICAL_HOST}` &&
    process.env.NODE_ENV === "production"
  ) {
    const url = request.nextUrl.clone();
    url.host = CANONICAL_HOST;
    url.protocol = "https";
    return NextResponse.redirect(url, 301);
  }

  if (!isProtectedPath(request.nextUrl.pathname)) {
    return NextResponse.next();
  }

  const token = await getToken({
    req: request,
    secret: getNextAuthSecret(),
  });

  const authorized = Boolean(token) && token?.emailVerified !== false;
  if (authorized) {
    return NextResponse.next();
  }

  const loginUrl = new URL("/auth/login", request.url);
  loginUrl.searchParams.set("callbackUrl", request.nextUrl.pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon\\.ico|.*\\.(?:png|jpg|svg|webp|ico|txt|xml)).*)"],
};

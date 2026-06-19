import { NextResponse } from "next/server";
import { isUnverifiedCredentialsLogin } from "@/lib/server/email-verification";

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as { email?: string; password?: string };
    const email = body.email?.trim() ?? "";
    const password = body.password ?? "";

    if (!email || !password) {
      return NextResponse.json({ unverified: false });
    }

    const unverified = await isUnverifiedCredentialsLogin(email, password);
    return NextResponse.json({ unverified });
  } catch {
    return NextResponse.json({ unverified: false });
  }
}

import { NextResponse } from "next/server";
import {
  findAuthUserById,
  registerCredentialsUser,
} from "@/lib/server/auth-users";
import {
  maskEmail,
  sendVerificationEmailForUser,
} from "@/lib/server/email-verification";
import { PersistentStoreNotConfiguredError } from "@/lib/server/persistent-store";

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as {
      email?: string;
      password?: string;
      name?: string;
    };

    const result = await registerCredentialsUser({
      email: body.email ?? "",
      password: body.password ?? "",
      name: body.name ?? "",
    });

    if (!result.ok) {
      return NextResponse.json({ error: result.error }, { status: 400 });
    }

    const user = await findAuthUserById(result.userId);
    const sent = await sendVerificationEmailForUser({
      userId: result.userId,
      email: result.email,
      name: user?.name ?? body.name ?? "Creator",
    });

    if (!sent.ok) {
      return NextResponse.json({ error: sent.error }, { status: 500 });
    }

    return NextResponse.json({
      ok: true,
      needsEmailVerification: true,
      email: maskEmail(result.email),
      linkedGoogleAccount: result.linkedGoogleAccount ?? false,
      emailDelivery: sent.delivery,
      emailSent: sent.emailSent,
      realInboxDelivery: sent.emailSent,
      devVerificationUrl: sent.emailSent ? undefined : sent.verifyUrl,
      deliveryError: sent.deliveryError,
    });
  } catch (err) {
    if (err instanceof PersistentStoreNotConfiguredError) {
      return NextResponse.json({ error: err.message }, { status: 503 });
    }
    return NextResponse.json(
      { error: "Could not create account. Try again." },
      { status: 500 }
    );
  }
}

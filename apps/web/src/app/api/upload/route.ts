import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth/auth-options";
import { proxyUploadToFastApi } from "@/lib/server/fastapi-proxy";
import {
  UploadValidationError,
  validateUploadFormData,
} from "@/lib/server/upload-guard";

export const runtime = "nodejs";
export const maxDuration = 120;

/**
 * Session-guarded upload gateway. Browser assets never hit FastAPI directly.
 */
export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json(
      { error: "Unauthorized. Sign in to upload studio assets." },
      { status: 401 }
    );
  }

  let formData: FormData;
  try {
    formData = await request.formData();
  } catch {
    return NextResponse.json(
      { error: "Invalid multipart upload payload." },
      { status: 400 }
    );
  }

  let outbound: FormData;
  try {
    ({ outbound } = validateUploadFormData(formData));
  } catch (error) {
    if (error instanceof UploadValidationError) {
      return NextResponse.json({ error: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : "Upload validation failed";
    return NextResponse.json({ error: message }, { status: 400 });
  }

  const proxyResult = await proxyUploadToFastApi(outbound);

  if (!proxyResult.ok) {
    const errorMessage =
      typeof proxyResult.data.error === "string"
        ? proxyResult.data.error
        : "Upload failed";

    return NextResponse.json(
      { error: errorMessage, ...proxyResult.data },
      { status: proxyResult.status }
    );
  }

  return NextResponse.json(proxyResult.data, { status: proxyResult.status });
}

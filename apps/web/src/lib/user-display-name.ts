type UserLike = {
  name?: string | null;
  email?: string | null;
};

/** Clean label for header pills — no broken comma fragments or email clipping. */
export function headerUserLabel(user: UserLike): string {
  const rawName = user.name?.trim();
  if (rawName) {
    const firstWord = rawName.split(/\s+/)[0]?.replace(/[,;:.!?]+$/u, "").trim();
    if (firstWord && firstWord.length >= 2) return firstWord;
    if (rawName.length <= 28) return rawName;
    return rawName.slice(0, 28).trim();
  }

  const email = user.email?.trim();
  if (email) {
    const local = email.split("@")[0] ?? "";
    const cleaned = local
      .replace(/[._+-]+/g, " ")
      .split(/\s+/)[0]
      ?.replace(/[,;:.!?]+$/u, "")
      .trim();
    if (cleaned) {
      return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
    }
  }

  return "Account";
}

/** Full display name for profile and account surfaces. */
export function profileDisplayName(user: UserLike): string {
  const rawName = user.name?.trim();
  if (rawName) return rawName;

  const email = user.email?.trim();
  if (email) {
    const local = email.split("@")[0] ?? "";
    if (local) {
      return local
        .replace(/[._+-]+/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase())
        .trim();
    }
  }

  return "Creator";
}

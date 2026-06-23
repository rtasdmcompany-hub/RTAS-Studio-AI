import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from "next-auth/providers/google";
import {
  getGoogleClientId,
  getGoogleClientSecret,
  getNextAuthSecret,
  getNextAuthUrl,
  isGoogleAuthConfigured,
} from "@/lib/env";
import {
  findAuthUserByEmail,
  findAuthUserById,
  isEmailVerified,
  upsertOAuthUser,
  verifyCredentials,
} from "@/lib/server/auth-users";

function toEmailVerifiedFlag(value: boolean | Date | null | undefined): boolean {
  if (value instanceof Date) return true;
  return value === true;
}

if (!process.env.NEXTAUTH_URL) {
  process.env.NEXTAUTH_URL = getNextAuthUrl();
}

export const authOptions: NextAuthOptions = {
  session: { strategy: "jwt", maxAge: 30 * 24 * 60 * 60 },
  pages: {
    signIn: "/auth/login",
    error: "/auth/login",
  },
  providers: [
    ...(isGoogleAuthConfigured()
      ? [
          GoogleProvider({
            clientId: getGoogleClientId(),
            clientSecret: getGoogleClientSecret(),
            allowDangerousEmailAccountLinking: true,
            authorization: {
              params: {
                prompt: "select_account",
                access_type: "offline",
                response_type: "code",
              },
            },
          }),
        ]
      : []),
    CredentialsProvider({
      name: "Email and password",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;

        const record = await findAuthUserByEmail(credentials.email);
        if (record && !isEmailVerified(record)) return null;

        const user = await verifyCredentials(
          credentials.email,
          credentials.password
        );
        if (!user) return null;

        return {
          id: user.id,
          email: user.email,
          name: user.name,
          image: user.image ?? undefined,
          emailVerified: true,
        };
      },
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider === "google" && user.email) {
        try {
          await upsertOAuthUser({
            id: user.id,
            email: user.email,
            name: user.name ?? user.email,
            image: user.image,
          });
        } catch (err) {
          console.error("Google sign-in: could not persist user record", err);
        }
      }

      if (account?.provider === "credentials") {
        const record = user.email
          ? await findAuthUserByEmail(user.email)
          : user.id
            ? await findAuthUserById(user.id)
            : null;
        if (record && !isEmailVerified(record)) {
          return "/auth/check-email?email=" + encodeURIComponent(record.email);
        }
      }

      return true;
    },

    async jwt({ token, user }) {
      if (user?.id) {
        token.sub = user.id;
        token.email = user.email;
        token.name = user.name;
        token.picture = user.image;
        token.emailVerified = toEmailVerifiedFlag(user.emailVerified);
      }

      if (token.sub) {
        try {
          const record = await findAuthUserById(token.sub);
          if (record) {
            token.name = record.name;
            token.email = record.email;
            token.picture = record.image ?? token.picture;
            token.emailVerified = isEmailVerified(record);
          }
        } catch (err) {
          console.error("JWT callback: could not refresh user from store", err);
        }
      }

      return token;
    },

    async session({ session, token }) {
      if (session.user && token.sub) {
        session.user.id = token.sub;
        session.user.email = token.email as string | undefined;
        session.user.name = token.name as string | undefined;
        session.user.image = token.picture as string | undefined;
        session.user.emailVerified = token.emailVerified === true;
      }

      return session;
    },
  },

  secret: getNextAuthSecret(),
  debug: process.env.NODE_ENV === "development",
};

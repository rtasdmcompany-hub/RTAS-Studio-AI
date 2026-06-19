import { withAuth } from "next-auth/middleware";

export default withAuth({
  pages: {
    signIn: "/auth/login",
  },
  callbacks: {
    authorized: ({ token }) => {
      if (!token) return false;
      return token.emailVerified !== false;
    },
  },
});

export const config = {
  matcher: ["/studio", "/studio/:path*", "/profile", "/profile/:path*"],
};

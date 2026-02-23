/**
 * NextAuth.js v5 configuration with Credentials, Google, and Facebook providers.
 * Authenticates against FastAPI backend.
 */

import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import Google from "next-auth/providers/google";
import Facebook from "next-auth/providers/facebook";

const API_URL =
  process.env.API_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8980";

// Enforce HTTPS in production (security check)
if (
  process.env.NODE_ENV === "production" &&
  API_URL.startsWith("http://") &&
  !API_URL.includes("localhost")
) {
  throw new Error(
    "SECURITY ERROR: API_URL must use HTTPS in production. Current value: " +
      API_URL
  );
}

export const { auth, handlers, signIn, signOut } = NextAuth({
  providers: [
    Google,
    Facebook,
    Credentials({
      credentials: {
        email: {},
        password: {},
      },
      async authorize(credentials) {
        const res = await fetch(`${API_URL}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: credentials?.email,
            password: credentials?.password,
          }),
        });
        const data = await res.json();
        if (data.success && data.data) {
          return {
            id: String(data.data.id),
            email: data.data.email,
            role: data.data.role,
          };
        }
        return null;
      },
    }),
  ],
  session: {
    strategy: "jwt",
    maxAge: 24 * 60 * 60, // 24 hours (NFR-SEC3)
  },
  pages: {
    signIn: "/login",
  },
  callbacks: {
    authorized({ auth }) {
      return !!auth;
    },
    async signIn({ user, account }) {
      if (account?.provider && account.provider !== "credentials") {
        try {
          const res = await fetch(`${API_URL}/api/auth/oauth`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: user.email,
              oauth_provider: account.provider,
              oauth_id: account.providerAccountId,
            }),
          });
          const data = await res.json();
          if (!data.success) {
            return `/login?error=OAuthAccountNotLinked`;
          }
          user.id = String(data.data.id);
          (user as { role?: string }).role = data.data.role;
          return true;
        } catch {
          return false;
        }
      }
      return true;
    },
    jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = (user as { role?: string }).role;
      }
      return token;
    },
    session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        (session.user as { role?: string }).role = token.role as string;
      }
      return session;
    },
  },
});

/**
 * NextAuth.js v5 route handler.
 * Re-exports GET and POST handlers from auth configuration.
 */

import { handlers } from "@/lib/auth";

export const { GET, POST } = handlers;

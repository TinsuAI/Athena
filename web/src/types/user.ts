/**
 * User related type definitions.
 */

export type UserRole = "user" | "admin";

export interface User {
  id: string;
  email: string;
  name: string | null;
  role: UserRole;
  created_at: string;
}

export interface Session {
  user: User;
  expires: string;
}

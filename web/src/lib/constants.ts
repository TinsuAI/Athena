/**
 * Application constants.
 */

export const APP_NAME = "Athena";
export const APP_DESCRIPTION = "HS Code Lookup Tool";

export const API_ENDPOINTS = {
  health: "/health",
  search: "/search",
  hsCode: "/hs-codes",
  favorites: "/favorites",
  history: "/history",
} as const;

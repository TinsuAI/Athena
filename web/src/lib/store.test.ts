import { describe, it, expect, beforeEach } from "vitest";
import { useStore } from "./store";
import type { SearchResult } from "@/types/hs-code";
import type { User } from "@/types/user";

describe("store - search slice", () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useStore.setState({
      searchQuery: "",
      searchResult: null,
      isSearching: false,
      searchError: null,
    });
  });

  describe("initial state", () => {
    it("has empty searchQuery", () => {
      expect(useStore.getState().searchQuery).toBe("");
    });

    it("has null searchResult", () => {
      expect(useStore.getState().searchResult).toBeNull();
    });

    it("has isSearching as false", () => {
      expect(useStore.getState().isSearching).toBe(false);
    });

    it("has searchError as null", () => {
      expect(useStore.getState().searchError).toBeNull();
    });
  });

  describe("setSearchQuery", () => {
    it("updates searchQuery", () => {
      useStore.getState().setSearchQuery("coffee beans");
      expect(useStore.getState().searchQuery).toBe("coffee beans");
    });

    it("handles Vietnamese diacritics", () => {
      useStore.getState().setSearchQuery("máy xay cà phê");
      expect(useStore.getState().searchQuery).toBe("máy xay cà phê");
    });
  });

  describe("setSearchResult", () => {
    const mockResult: SearchResult = {
      hs_code: "0901.11.00",
      description: "Coffee, not roasted",
      duty_rate: "5%",
      vat_rate: "10%",
      classification: {
        material: "Coffee beans",
        function: "Beverage raw material",
      },
      practical_notes: ["Requires phytosanitary certificate"],
      confidence: 95,
    };

    it("updates searchResult", () => {
      useStore.getState().setSearchResult(mockResult);
      expect(useStore.getState().searchResult).toEqual(mockResult);
    });

    it("clears searchError when setting result", () => {
      useStore.setState({ searchError: "Previous error" });
      useStore.getState().setSearchResult(mockResult);
      expect(useStore.getState().searchError).toBeNull();
    });

    it("can set result to null", () => {
      useStore.setState({ searchResult: mockResult });
      useStore.getState().setSearchResult(null);
      expect(useStore.getState().searchResult).toBeNull();
    });
  });

  describe("setIsSearching", () => {
    it("sets isSearching to true", () => {
      useStore.getState().setIsSearching(true);
      expect(useStore.getState().isSearching).toBe(true);
    });

    it("sets isSearching to false", () => {
      useStore.setState({ isSearching: true });
      useStore.getState().setIsSearching(false);
      expect(useStore.getState().isSearching).toBe(false);
    });
  });

  describe("setSearchError", () => {
    it("sets error message", () => {
      useStore.getState().setSearchError("Network error");
      expect(useStore.getState().searchError).toBe("Network error");
    });

    it("clears error when set to null", () => {
      useStore.setState({ searchError: "Previous error" });
      useStore.getState().setSearchError(null);
      expect(useStore.getState().searchError).toBeNull();
    });
  });

  describe("clearSearch", () => {
    it("clears searchQuery, searchResult, and searchError", () => {
      // Set up state with values
      useStore.setState({
        searchQuery: "coffee",
        searchResult: {
          hs_code: "0901",
          description: "Coffee",
          duty_rate: "5%",
          vat_rate: "10%",
          classification: { material: "Coffee", function: "Beverage" },
          practical_notes: [],
          confidence: 90,
        },
        searchError: "Some error",
      });

      // Clear
      useStore.getState().clearSearch();

      expect(useStore.getState().searchQuery).toBe("");
      expect(useStore.getState().searchResult).toBeNull();
      expect(useStore.getState().searchError).toBeNull();
    });

    it("does not affect isSearching state", () => {
      useStore.setState({ isSearching: true });
      useStore.getState().clearSearch();
      // isSearching should remain unchanged
      expect(useStore.getState().isSearching).toBe(true);
    });
  });
});

describe("store - auth slice", () => {
  beforeEach(() => {
    useStore.setState({
      isAuthenticated: false,
      user: null,
    });
  });

  describe("logout", () => {
    it("resets isAuthenticated to false and user to null", () => {
      const testUser: User = {
        id: "1",
        email: "test@example.com",
        name: null,
        role: "user",
        created_at: "2026-01-01",
      };

      useStore.setState({
        isAuthenticated: true,
        user: testUser,
      });

      useStore.getState().logout();

      expect(useStore.getState().isAuthenticated).toBe(false);
      expect(useStore.getState().user).toBeNull();
    });

    it("is a no-op when already logged out", () => {
      useStore.getState().logout();

      expect(useStore.getState().isAuthenticated).toBe(false);
      expect(useStore.getState().user).toBeNull();
    });
  });
});

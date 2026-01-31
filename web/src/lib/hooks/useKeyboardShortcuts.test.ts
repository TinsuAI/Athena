import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useKeyboardShortcuts } from "./useKeyboardShortcuts";

describe("useKeyboardShortcuts", () => {
  let mockInputRef: { current: HTMLInputElement | null };
  let mockInput: HTMLInputElement;

  beforeEach(() => {
    mockInput = document.createElement("input");
    mockInput.focus = vi.fn();
    mockInputRef = { current: mockInput };
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("slash key shortcut", () => {
    it('focuses input when "/" is pressed outside of input', () => {
      renderHook(() => useKeyboardShortcuts({ inputRef: mockInputRef }));

      const event = new KeyboardEvent("keydown", {
        key: "/",
        bubbles: true,
      });

      // Simulate pressing / on body
      Object.defineProperty(event, "target", {
        value: document.body,
        writable: false,
      });

      document.dispatchEvent(event);

      expect(mockInput.focus).toHaveBeenCalledTimes(1);
    });

    it('does not focus input when "/" is pressed inside another input', () => {
      renderHook(() => useKeyboardShortcuts({ inputRef: mockInputRef }));

      const anotherInput = document.createElement("input");
      const event = new KeyboardEvent("keydown", {
        key: "/",
        bubbles: true,
      });

      Object.defineProperty(event, "target", {
        value: anotherInput,
        writable: false,
      });

      document.dispatchEvent(event);

      expect(mockInput.focus).not.toHaveBeenCalled();
    });

    it('does not focus input when "/" is pressed inside textarea', () => {
      renderHook(() => useKeyboardShortcuts({ inputRef: mockInputRef }));

      const textarea = document.createElement("textarea");
      const event = new KeyboardEvent("keydown", {
        key: "/",
        bubbles: true,
      });

      Object.defineProperty(event, "target", {
        value: textarea,
        writable: false,
      });

      document.dispatchEvent(event);

      expect(mockInput.focus).not.toHaveBeenCalled();
    });
  });

  describe("Cmd+K / Ctrl+K shortcut", () => {
    it("focuses input when Cmd+K is pressed (Mac)", () => {
      renderHook(() => useKeyboardShortcuts({ inputRef: mockInputRef }));

      const event = new KeyboardEvent("keydown", {
        key: "k",
        metaKey: true,
        bubbles: true,
      });

      Object.defineProperty(event, "target", {
        value: document.body,
        writable: false,
      });

      document.dispatchEvent(event);

      expect(mockInput.focus).toHaveBeenCalledTimes(1);
    });

    it("focuses input when Ctrl+K is pressed (Windows)", () => {
      renderHook(() => useKeyboardShortcuts({ inputRef: mockInputRef }));

      const event = new KeyboardEvent("keydown", {
        key: "k",
        ctrlKey: true,
        bubbles: true,
      });

      Object.defineProperty(event, "target", {
        value: document.body,
        writable: false,
      });

      document.dispatchEvent(event);

      expect(mockInput.focus).toHaveBeenCalledTimes(1);
    });

    it("focuses input when Cmd+K is pressed even from another input", () => {
      renderHook(() => useKeyboardShortcuts({ inputRef: mockInputRef }));

      const anotherInput = document.createElement("input");
      const event = new KeyboardEvent("keydown", {
        key: "k",
        metaKey: true,
        bubbles: true,
      });

      Object.defineProperty(event, "target", {
        value: anotherInput,
        writable: false,
      });

      document.dispatchEvent(event);

      // Cmd+K should work even in inputs
      expect(mockInput.focus).toHaveBeenCalledTimes(1);
    });

    it("does not focus when just K is pressed without modifier", () => {
      renderHook(() => useKeyboardShortcuts({ inputRef: mockInputRef }));

      const event = new KeyboardEvent("keydown", {
        key: "k",
        bubbles: true,
      });

      Object.defineProperty(event, "target", {
        value: document.body,
        writable: false,
      });

      document.dispatchEvent(event);

      expect(mockInput.focus).not.toHaveBeenCalled();
    });
  });

  describe("enabled option", () => {
    it("does not set up shortcuts when enabled is false", () => {
      renderHook(() =>
        useKeyboardShortcuts({ inputRef: mockInputRef, enabled: false })
      );

      const event = new KeyboardEvent("keydown", {
        key: "/",
        bubbles: true,
      });

      Object.defineProperty(event, "target", {
        value: document.body,
        writable: false,
      });

      document.dispatchEvent(event);

      expect(mockInput.focus).not.toHaveBeenCalled();
    });
  });

  describe("cleanup", () => {
    it("removes event listener on unmount", () => {
      const removeEventListenerSpy = vi.spyOn(document, "removeEventListener");

      const { unmount } = renderHook(() =>
        useKeyboardShortcuts({ inputRef: mockInputRef })
      );

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        "keydown",
        expect.any(Function)
      );

      removeEventListenerSpy.mockRestore();
    });
  });
});

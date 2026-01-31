import { useEffect, useCallback, RefObject } from "react";

interface UseKeyboardShortcutsOptions {
  inputRef: RefObject<HTMLInputElement | null>;
  enabled?: boolean;
}

/**
 * Custom hook that sets up keyboard shortcuts for focusing the search bar.
 * - "/" key focuses the search bar (common pattern)
 * - Cmd+K (Mac) / Ctrl+K (Windows) focuses the search bar
 *
 * Shortcuts are disabled when already typing in an input/textarea.
 */
export function useKeyboardShortcuts({
  inputRef,
  enabled = true,
}: UseKeyboardShortcutsOptions): void {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!enabled) return;

      const target = e.target as HTMLElement;
      const tagName = target.tagName.toLowerCase();
      const isEditable =
        target.isContentEditable ||
        tagName === "input" ||
        tagName === "textarea" ||
        tagName === "select";

      // "/" key to focus - only when not in an input
      if (e.key === "/" && !isEditable) {
        e.preventDefault();
        inputRef.current?.focus();
        return;
      }

      // Cmd+K (Mac) or Ctrl+K (Windows) to focus - works even in inputs
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        inputRef.current?.focus();
        return;
      }
    },
    [inputRef, enabled]
  );

  useEffect(() => {
    if (!enabled) return;

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown, enabled]);
}

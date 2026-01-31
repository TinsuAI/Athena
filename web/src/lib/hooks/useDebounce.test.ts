import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useDebounce } from "./useDebounce";

describe("useDebounce", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns initial value immediately", () => {
    const { result } = renderHook(() => useDebounce("initial", 150));
    expect(result.current).toBe("initial");
  });

  it("debounces value changes by default delay (150ms)", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 150),
      { initialProps: { value: "initial" } }
    );

    // Change value
    rerender({ value: "updated" });

    // Value should not have changed yet
    expect(result.current).toBe("initial");

    // Fast forward 100ms (not enough)
    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(result.current).toBe("initial");

    // Fast forward remaining 50ms
    act(() => {
      vi.advanceTimersByTime(50);
    });
    expect(result.current).toBe("updated");
  });

  it("resets timer on rapid changes", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 150),
      { initialProps: { value: "a" } }
    );

    // Simulate rapid typing
    rerender({ value: "ab" });
    act(() => {
      vi.advanceTimersByTime(50);
    });

    rerender({ value: "abc" });
    act(() => {
      vi.advanceTimersByTime(50);
    });

    rerender({ value: "abcd" });
    act(() => {
      vi.advanceTimersByTime(50);
    });

    // Value should still be initial
    expect(result.current).toBe("a");

    // Fast forward full debounce time
    act(() => {
      vi.advanceTimersByTime(150);
    });

    // Now it should be the last value
    expect(result.current).toBe("abcd");
  });

  it("respects custom delay", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: "initial" } }
    );

    rerender({ value: "updated" });

    // 150ms (default) should not be enough
    act(() => {
      vi.advanceTimersByTime(150);
    });
    expect(result.current).toBe("initial");

    // 500ms should update
    act(() => {
      vi.advanceTimersByTime(350);
    });
    expect(result.current).toBe("updated");
  });

  it("handles object values", () => {
    const obj1 = { query: "coffee" };
    const obj2 = { query: "tea" };

    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 150),
      { initialProps: { value: obj1 } }
    );

    rerender({ value: obj2 });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    expect(result.current).toBe(obj2);
  });

  it("cleans up timer on unmount", () => {
    const { unmount } = renderHook(() => useDebounce("test", 150));

    // This should not throw
    unmount();

    act(() => {
      vi.advanceTimersByTime(200);
    });
  });
});

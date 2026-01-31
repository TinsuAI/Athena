import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SearchBar } from "./SearchBar";

describe("SearchBar", () => {
  const defaultProps = {
    value: "",
    onChange: vi.fn(),
    onSearch: vi.fn(),
    onClear: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("rendering", () => {
    it("renders search input", () => {
      render(<SearchBar {...defaultProps} />);
      expect(screen.getByTestId("search-input")).toBeInTheDocument();
    });

    it("renders search button", () => {
      render(<SearchBar {...defaultProps} />);
      expect(screen.getByTestId("search-button")).toBeInTheDocument();
    });

    it("renders loading spinner in button when isLoading is true", () => {
      render(<SearchBar {...defaultProps} isLoading={true} value="test" />);
      expect(screen.getByTestId("search-spinner")).toBeInTheDocument();
    });

    it("renders clear button when value is present", () => {
      render(<SearchBar {...defaultProps} value="test" />);
      expect(screen.getByTestId("clear-button")).toBeInTheDocument();
    });

    it("hides clear button when value is empty", () => {
      render(<SearchBar {...defaultProps} value="" />);
      expect(screen.queryByTestId("clear-button")).not.toBeInTheDocument();
    });

    it("displays custom placeholder", () => {
      render(<SearchBar {...defaultProps} placeholder="Custom placeholder" />);
      expect(screen.getByPlaceholderText("Custom placeholder")).toBeInTheDocument();
    });

    it("displays default placeholder with keyboard shortcut hint", () => {
      render(<SearchBar {...defaultProps} />);
      expect(screen.getByPlaceholderText(/Press "\/"/)).toBeInTheDocument();
    });

    it("disables search button when value is empty", () => {
      render(<SearchBar {...defaultProps} value="" />);
      expect(screen.getByTestId("search-button")).toBeDisabled();
    });

    it("enables search button when value has text", () => {
      render(<SearchBar {...defaultProps} value="coffee" />);
      expect(screen.getByTestId("search-button")).not.toBeDisabled();
    });

    it("disables search button when loading", () => {
      render(<SearchBar {...defaultProps} value="coffee" isLoading={true} />);
      expect(screen.getByTestId("search-button")).toBeDisabled();
    });
  });

  describe("auto-focus", () => {
    it("auto-focuses input on mount by default", () => {
      render(<SearchBar {...defaultProps} />);
      expect(screen.getByTestId("search-input")).toHaveFocus();
    });

    it("does not auto-focus when autoFocus is false", () => {
      render(<SearchBar {...defaultProps} autoFocus={false} />);
      expect(screen.getByTestId("search-input")).not.toHaveFocus();
    });
  });

  describe("user interactions", () => {
    it("calls onChange when typing", async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      render(<SearchBar {...defaultProps} onChange={onChange} />);

      const input = screen.getByTestId("search-input");
      await user.type(input, "coffee");

      expect(onChange).toHaveBeenCalledTimes(6); // Once per character
      expect(onChange).toHaveBeenNthCalledWith(1, "c");
    });

    it("calls onSearch when search button is clicked", async () => {
      const user = userEvent.setup();
      const onSearch = vi.fn();
      render(<SearchBar {...defaultProps} value="coffee" onSearch={onSearch} />);

      await user.click(screen.getByTestId("search-button"));
      expect(onSearch).toHaveBeenCalledTimes(1);
    });

    it("calls onSearch when Enter is pressed", () => {
      const onSearch = vi.fn();
      render(<SearchBar {...defaultProps} value="coffee" onSearch={onSearch} />);

      const input = screen.getByTestId("search-input");
      fireEvent.keyDown(input, { key: "Enter" });

      expect(onSearch).toHaveBeenCalledTimes(1);
    });

    it("does not call onSearch when Enter is pressed with empty value", () => {
      const onSearch = vi.fn();
      render(<SearchBar {...defaultProps} value="" onSearch={onSearch} />);

      const input = screen.getByTestId("search-input");
      fireEvent.keyDown(input, { key: "Enter" });

      expect(onSearch).not.toHaveBeenCalled();
    });

    it("calls onClear when clear button is clicked", async () => {
      const user = userEvent.setup();
      const onClear = vi.fn();
      render(<SearchBar {...defaultProps} value="test" onClear={onClear} />);

      await user.click(screen.getByTestId("clear-button"));
      expect(onClear).toHaveBeenCalledTimes(1);
    });

    it("calls onClear when Escape key is pressed", () => {
      const onClear = vi.fn();
      render(<SearchBar {...defaultProps} value="test" onClear={onClear} />);

      const input = screen.getByTestId("search-input");
      fireEvent.keyDown(input, { key: "Escape" });

      expect(onClear).toHaveBeenCalledTimes(1);
    });

    it("maintains focus after clearing", async () => {
      const user = userEvent.setup();
      render(<SearchBar {...defaultProps} value="test" />);

      await user.click(screen.getByTestId("clear-button"));
      expect(screen.getByTestId("search-input")).toHaveFocus();
    });
  });

  describe("Vietnamese diacritics handling", () => {
    it("accepts Vietnamese text with diacritics", async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      render(<SearchBar {...defaultProps} onChange={onChange} />);

      const input = screen.getByTestId("search-input");
      await user.type(input, "máy xay");

      // Verify Vietnamese characters are handled
      expect(onChange).toHaveBeenCalled();
      expect(onChange).toHaveBeenNthCalledWith(1, "m");
    });

    it("displays Vietnamese text correctly", () => {
      render(<SearchBar {...defaultProps} value="máy xay cà phê" />);
      const input = screen.getByTestId("search-input") as HTMLInputElement;
      expect(input.value).toBe("máy xay cà phê");
    });
  });

  describe("accessibility", () => {
    it("has aria-label for search input", () => {
      render(<SearchBar {...defaultProps} />);
      expect(screen.getByLabelText("Search HS codes")).toBeInTheDocument();
    });

    it("has aria-label for clear button", () => {
      render(<SearchBar {...defaultProps} value="test" />);
      expect(screen.getByLabelText("Clear search")).toBeInTheDocument();
    });

    it("has aria-label for loading spinner", () => {
      render(<SearchBar {...defaultProps} isLoading={true} value="test" />);
      expect(screen.getByLabelText("Searching...")).toBeInTheDocument();
    });
  });
});

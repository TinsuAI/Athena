"""Tests for TariffHierarchyParser category context tracking."""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from app.services.tariff_hierarchy_parser import (
    TariffHierarchyParser,
    HSCodeData,
    TariffHierarchy,
)


class TestCategoryContextTracking:
    """Test cases for category indicator row capture and context appending."""

    def test_detect_category_indicator_row(self):
        """Category rows (no code, starts with dash) should be detected."""
        # Category indicator rows have:
        # - No 8-digit code (code_val is None)
        # - Description starts with "- "
        # - Often ends with ":" (but not always)

        # Create mock worksheet with category indicator row
        mock_rows = [
            # Header rows (skip)
            (None, None, None, None, None, None, None, None),
            # Category indicator: "- Từ tre:" (From bamboo)
            (None, None, None, None, None, None, "- Từ tre:", "- Of bamboo:"),
            # 8-digit HS code under bamboo category
            (None, None, None, None, None, "44191200", "- - Đũa", "- - Chopsticks"),
            # Another 8-digit HS code under bamboo category
            (None, None, None, None, None, "44191900", "- - Loại khác", "- - Other"),
        ]

        with patch.object(TariffHierarchyParser, '__init__', lambda x, y: None):
            parser = TariffHierarchyParser.__new__(TariffHierarchyParser)
            parser.sheet = MagicMock()
            parser.sheet.iter_rows = MagicMock(return_value=iter(mock_rows))

            hierarchy = parser.parse_hierarchy()

            # Find the "Other" HS code - should have bamboo context
            other_code = next((hc for hc in hierarchy.hs_codes if hc.code == "44191900"), None)

            assert other_code is not None
            assert "Từ tre" in other_code.description_vn or "bamboo" in other_code.description_vn.lower()

    def test_bamboo_item_context_appended(self):
        """AC2: HS code 4419.19.00 should include bamboo category context."""
        mock_rows = [
            (None, None, None, None, None, None, None, None),
            # 4-digit heading
            (None, None, None, None, None, "4419", "Đồ dùng để bàn và đồ dùng nhà bếp, bằng gỗ", "Tableware and kitchenware, of wood"),
            # Category indicator: "- Từ tre:" (From bamboo)
            (None, None, None, None, None, None, "- Từ tre:", "- Of bamboo:"),
            # 6-digit subheading
            (None, None, None, None, None, "441919", "- - Loại khác", "- - Other"),
            # 8-digit HS code under bamboo
            (None, None, None, None, None, "44191900", "- - Loại khác", "- - Other"),
        ]

        with patch.object(TariffHierarchyParser, '__init__', lambda x, y: None):
            parser = TariffHierarchyParser.__new__(TariffHierarchyParser)
            parser.sheet = MagicMock()
            parser.sheet.iter_rows = MagicMock(return_value=iter(mock_rows))

            hierarchy = parser.parse_hierarchy()

            other_code = next((hc for hc in hierarchy.hs_codes if hc.code == "44191900"), None)

            assert other_code is not None
            # Should contain category context in brackets
            assert "[" in other_code.description_vn
            assert "Từ tre" in other_code.description_vn

    def test_non_bamboo_item_context(self):
        """AC3: HS code 4419.90.00 should include non-bamboo context."""
        # The category applies to HS codes at GREATER indent levels
        # Category at indent 1 applies to HS codes at indent 2+
        mock_rows = [
            (None, None, None, None, None, None, None, None),
            # 4-digit heading
            (None, None, None, None, None, "4419", "Đồ dùng để bàn và đồ dùng nhà bếp, bằng gỗ", "Tableware and kitchenware, of wood"),
            # Category indicator at indent 1: "- Loại khác:" (Other - not bamboo/tropical)
            (None, None, None, None, None, None, "- Loại khác:", "- Other:"),
            # 6-digit subheading at indent 2 (under "other" category)
            (None, None, None, None, None, "441990", "- - Loại khác", "- - Other"),
            # 8-digit HS code at indent 2 under "other" category
            (None, None, None, None, None, "44199000", "- - Loại khác", "- - Other"),
        ]

        with patch.object(TariffHierarchyParser, '__init__', lambda x, y: None):
            parser = TariffHierarchyParser.__new__(TariffHierarchyParser)
            parser.sheet = MagicMock()
            parser.sheet.iter_rows = MagicMock(return_value=iter(mock_rows))

            hierarchy = parser.parse_hierarchy()

            other_code = next((hc for hc in hierarchy.hs_codes if hc.code == "44199000"), None)

            assert other_code is not None
            # Should contain category context
            assert "[" in other_code.description_vn

    def test_category_stack_pops_on_indent_decrease(self):
        """Category stack should pop when moving to sibling or parent level."""
        mock_rows = [
            (None, None, None, None, None, None, None, None),
            # 4-digit heading
            (None, None, None, None, None, "4419", "Đồ dùng", "Tableware"),
            # Category 1: bamboo (indent 1)
            (None, None, None, None, None, None, "- Từ tre:", "- Of bamboo:"),
            # HS code under bamboo (indent 2)
            (None, None, None, None, None, "44191200", "- - Đũa", "- - Chopsticks"),
            # Category 2: other (indent 1 - sibling, should pop bamboo)
            (None, None, None, None, None, None, "- Loại khác:", "- Other:"),
            # HS code under "other" category (indent 2)
            (None, None, None, None, None, "44199000", "- - Loại khác", "- - Other"),
        ]

        with patch.object(TariffHierarchyParser, '__init__', lambda x, y: None):
            parser = TariffHierarchyParser.__new__(TariffHierarchyParser)
            parser.sheet = MagicMock()
            parser.sheet.iter_rows = MagicMock(return_value=iter(mock_rows))

            hierarchy = parser.parse_hierarchy()

            # Bamboo chopsticks should have bamboo context (positive)
            chopsticks = next((hc for hc in hierarchy.hs_codes if hc.code == "44191200"), None)
            assert chopsticks is not None
            assert "[Từ tre]" in chopsticks.description_vn

            # "Other" should have "other" context (positive), NOT bamboo positive context
            other_code = next((hc for hc in hierarchy.hs_codes if hc.code == "44199000"), None)
            assert other_code is not None
            assert "[Loại khác]" in other_code.description_vn  # Positive context from "other" category
            assert "[Từ tre]" not in other_code.description_vn  # No bamboo positive context

    def test_category_stack_clears_on_new_heading(self):
        """Category stack should clear when encountering a new 4-digit heading."""
        mock_rows = [
            (None, None, None, None, None, None, None, None),
            # First heading
            (None, None, None, None, None, "4419", "Đồ dùng gỗ", "Wooden items"),
            # Category under first heading
            (None, None, None, None, None, None, "- Từ tre:", "- Of bamboo:"),
            # HS code under bamboo
            (None, None, None, None, None, "44191200", "- - Đũa", "- - Chopsticks"),
            # NEW 4-digit heading - should clear category stack
            (None, None, None, None, None, "4420", "Đồ gỗ khảm", "Wood marquetry"),
            # HS code under new heading - should NOT have bamboo context
            (None, None, None, None, None, "44201000", "- Tượng nhỏ", "- Statuettes"),
        ]

        with patch.object(TariffHierarchyParser, '__init__', lambda x, y: None):
            parser = TariffHierarchyParser.__new__(TariffHierarchyParser)
            parser.sheet = MagicMock()
            parser.sheet.iter_rows = MagicMock(return_value=iter(mock_rows))

            hierarchy = parser.parse_hierarchy()

            # Statuettes under new heading should NOT have bamboo context
            statuettes = next((hc for hc in hierarchy.hs_codes if hc.code == "44201000"), None)
            assert statuettes is not None
            assert "Từ tre" not in statuettes.description_vn
            assert "bamboo" not in statuettes.description_vn.lower()

    def test_nested_categories(self):
        """Nested categories should stack properly."""
        mock_rows = [
            (None, None, None, None, None, None, None, None),
            # Heading
            (None, None, None, None, None, "7418", "Đồ vệ sinh", "Sanitary ware"),
            # Parent category: copper (indent 1)
            (None, None, None, None, None, None, "- Bằng đồng:", "- Of copper:"),
            # Nested category: bathroom (indent 2)
            (None, None, None, None, None, None, "- - Đồ dùng nhà tắm:", "- - Bathroom fittings:"),
            # HS code under nested categories
            (None, None, None, None, None, "74182000", "- - - Bộ trộn", "- - - Mixers"),
        ]

        with patch.object(TariffHierarchyParser, '__init__', lambda x, y: None):
            parser = TariffHierarchyParser.__new__(TariffHierarchyParser)
            parser.sheet = MagicMock()
            parser.sheet.iter_rows = MagicMock(return_value=iter(mock_rows))

            hierarchy = parser.parse_hierarchy()

            mixers = next((hc for hc in hierarchy.hs_codes if hc.code == "74182000"), None)
            assert mixers is not None
            # Should have both category contexts
            assert "đồng" in mixers.description_vn.lower() or "copper" in mixers.description_vn.lower()

    def test_category_without_english_translation(self):
        """Categories without English translation should still work."""
        mock_rows = [
            (None, None, None, None, None, None, None, None),
            # Heading
            (None, None, None, None, None, "4419", "Đồ dùng", "Tableware"),
            # Category with no English
            (None, None, None, None, None, None, "- Từ tre:", None),
            # HS code
            (None, None, None, None, None, "44191200", "- - Đũa", "- - Chopsticks"),
        ]

        with patch.object(TariffHierarchyParser, '__init__', lambda x, y: None):
            parser = TariffHierarchyParser.__new__(TariffHierarchyParser)
            parser.sheet = MagicMock()
            parser.sheet.iter_rows = MagicMock(return_value=iter(mock_rows))

            hierarchy = parser.parse_hierarchy()

            chopsticks = next((hc for hc in hierarchy.hs_codes if hc.code == "44191200"), None)
            assert chopsticks is not None
            assert "Từ tre" in chopsticks.description_vn

    def test_count_leading_dashes(self):
        """Test the _count_leading_dashes helper method."""
        with patch.object(TariffHierarchyParser, '__init__', lambda x, y: None):
            parser = TariffHierarchyParser.__new__(TariffHierarchyParser)

            assert parser._count_leading_dashes("No dashes") == 0
            assert parser._count_leading_dashes("- One dash") == 1
            assert parser._count_leading_dashes("- - Two dashes") == 2
            assert parser._count_leading_dashes("- - - Three dashes") == 3

    def test_negative_context_for_other_codes(self):
        """'Other' codes without category should get negative context listing sibling categories."""
        mock_rows = [
            (None, None, None, None, None, None, None, None),
            # 4-digit heading
            (None, None, None, None, None, "4419", "Đồ dùng để bàn và đồ dùng nhà bếp, bằng gỗ", "Tableware and kitchenware, of wood"),
            # Category indicator: bamboo (indent 1)
            (None, None, None, None, None, None, "- Từ tre:", "- Of bamboo:"),
            # HS code under bamboo
            (None, None, None, None, None, "44191200", "- - Đũa", "- - Chopsticks"),
            # Another HS code that's "Other" but at top level (no category applies)
            # This is at indent 1, same as category, so category doesn't apply
            (None, None, None, None, None, "44199000", "- Loại khác", "- Other"),
        ]

        with patch.object(TariffHierarchyParser, '__init__', lambda x, y: None):
            parser = TariffHierarchyParser.__new__(TariffHierarchyParser)
            parser.sheet = MagicMock()
            parser.sheet.iter_rows = MagicMock(return_value=iter(mock_rows))

            hierarchy = parser.parse_hierarchy()

            # "Other" code should have negative context excluding bamboo
            other_code = next((hc for hc in hierarchy.hs_codes if hc.code == "44199000"), None)
            assert other_code is not None
            assert "không thuộc" in other_code.description_vn
            assert "Từ tre" in other_code.description_vn

            # Bamboo chopsticks should still have positive context
            chopsticks = next((hc for hc in hierarchy.hs_codes if hc.code == "44191200"), None)
            assert chopsticks is not None
            assert "[Từ tre]" in chopsticks.description_vn

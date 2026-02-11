"""Tests for TariffHierarchyParser category context tracking and expanded parsing."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from decimal import Decimal

from app.services.tariff_hierarchy_parser import (
    TariffHierarchyParser,
    HSCodeData,
    FTARateData,
    TariffHierarchy,
)


def _make_parser() -> TariffHierarchyParser:
    """Create a parser instance with mocked __init__."""
    with patch.object(TariffHierarchyParser, '__init__', lambda x, y: None):
        parser = TariffHierarchyParser.__new__(TariffHierarchyParser)
        parser.sheet = MagicMock()
        return parser


def _run_parse(parser: TariffHierarchyParser, mock_rows: list[tuple]) -> TariffHierarchy:
    """Set mock rows and run parse_hierarchy."""
    parser.sheet.iter_rows = MagicMock(return_value=iter(mock_rows))
    return parser.parse_hierarchy()


class TestCategoryContextTracking:
    """Test cases for category indicator row capture and context appending."""

    def test_detect_category_indicator_row(self):
        """Category rows (no code, starts with dash) should be detected."""
        mock_rows = [
            (None, None, None, None, None, None, None, None),
            (None, None, None, None, None, None, "- Từ tre:", "- Of bamboo:"),
            (None, None, None, None, None, "44191200", "- - Đũa", "- - Chopsticks"),
            (None, None, None, None, None, "44191900", "- - Loại khác", "- - Other"),
        ]

        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        other_code = next((hc for hc in hierarchy.hs_codes if hc.code == "44191900"), None)
        assert other_code is not None
        assert "Từ tre" in other_code.description_vn or "bamboo" in other_code.description_vn.lower()

    def test_bamboo_item_context_appended(self):
        """AC2: HS code 4419.19.00 should include bamboo category context."""
        mock_rows = [
            (None, None, None, None, None, None, None, None),
            (None, None, None, None, None, "4419", "Đồ dùng để bàn và đồ dùng nhà bếp, bằng gỗ", "Tableware and kitchenware, of wood"),
            (None, None, None, None, None, None, "- Từ tre:", "- Of bamboo:"),
            (None, None, None, None, None, "441919", "- - Loại khác", "- - Other"),
            (None, None, None, None, None, "44191900", "- - Loại khác", "- - Other"),
        ]

        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        other_code = next((hc for hc in hierarchy.hs_codes if hc.code == "44191900"), None)
        assert other_code is not None
        assert "[" in other_code.description_vn
        assert "Từ tre" in other_code.description_vn

    def test_non_bamboo_item_context(self):
        """AC3: HS code 4419.90.00 should include non-bamboo context."""
        mock_rows = [
            (None, None, None, None, None, None, None, None),
            (None, None, None, None, None, "4419", "Đồ dùng để bàn và đồ dùng nhà bếp, bằng gỗ", "Tableware and kitchenware, of wood"),
            (None, None, None, None, None, None, "- Loại khác:", "- Other:"),
            (None, None, None, None, None, "441990", "- - Loại khác", "- - Other"),
            (None, None, None, None, None, "44199000", "- - Loại khác", "- - Other"),
        ]

        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        other_code = next((hc for hc in hierarchy.hs_codes if hc.code == "44199000"), None)
        assert other_code is not None
        assert "[" in other_code.description_vn

    def test_category_stack_pops_on_indent_decrease(self):
        """Category stack should pop when moving to sibling or parent level."""
        mock_rows = [
            (None, None, None, None, None, None, None, None),
            (None, None, None, None, None, "4419", "Đồ dùng", "Tableware"),
            (None, None, None, None, None, None, "- Từ tre:", "- Of bamboo:"),
            (None, None, None, None, None, "44191200", "- - Đũa", "- - Chopsticks"),
            (None, None, None, None, None, None, "- Loại khác:", "- Other:"),
            (None, None, None, None, None, "44199000", "- - Loại khác", "- - Other"),
        ]

        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        chopsticks = next((hc for hc in hierarchy.hs_codes if hc.code == "44191200"), None)
        assert chopsticks is not None
        assert "[Từ tre]" in chopsticks.description_vn

        other_code = next((hc for hc in hierarchy.hs_codes if hc.code == "44199000"), None)
        assert other_code is not None
        assert "[Loại khác]" in other_code.description_vn
        assert "[Từ tre]" not in other_code.description_vn

    def test_category_stack_clears_on_new_heading(self):
        """Category stack should clear when encountering a new 4-digit heading."""
        mock_rows = [
            (None, None, None, None, None, None, None, None),
            (None, None, None, None, None, "4419", "Đồ dùng gỗ", "Wooden items"),
            (None, None, None, None, None, None, "- Từ tre:", "- Of bamboo:"),
            (None, None, None, None, None, "44191200", "- - Đũa", "- - Chopsticks"),
            (None, None, None, None, None, "4420", "Đồ gỗ khảm", "Wood marquetry"),
            (None, None, None, None, None, "44201000", "- Tượng nhỏ", "- Statuettes"),
        ]

        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        statuettes = next((hc for hc in hierarchy.hs_codes if hc.code == "44201000"), None)
        assert statuettes is not None
        assert "Từ tre" not in statuettes.description_vn
        assert "bamboo" not in statuettes.description_vn.lower()

    def test_nested_categories(self):
        """Nested categories should stack properly."""
        mock_rows = [
            (None, None, None, None, None, None, None, None),
            (None, None, None, None, None, "7418", "Đồ vệ sinh", "Sanitary ware"),
            (None, None, None, None, None, None, "- Bằng đồng:", "- Of copper:"),
            (None, None, None, None, None, None, "- - Đồ dùng nhà tắm:", "- - Bathroom fittings:"),
            (None, None, None, None, None, "74182000", "- - - Bộ trộn", "- - - Mixers"),
        ]

        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        mixers = next((hc for hc in hierarchy.hs_codes if hc.code == "74182000"), None)
        assert mixers is not None
        assert "đồng" in mixers.description_vn.lower() or "copper" in mixers.description_vn.lower()

    def test_category_without_english_translation(self):
        """Categories without English translation should still work."""
        mock_rows = [
            (None, None, None, None, None, None, None, None),
            (None, None, None, None, None, "4419", "Đồ dùng", "Tableware"),
            (None, None, None, None, None, None, "- Từ tre:", None),
            (None, None, None, None, None, "44191200", "- - Đũa", "- - Chopsticks"),
        ]

        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        chopsticks = next((hc for hc in hierarchy.hs_codes if hc.code == "44191200"), None)
        assert chopsticks is not None
        assert "Từ tre" in chopsticks.description_vn

    def test_count_leading_dashes(self):
        """Test the _count_leading_dashes helper method."""
        parser = _make_parser()
        assert parser._count_leading_dashes("No dashes") == 0
        assert parser._count_leading_dashes("- One dash") == 1
        assert parser._count_leading_dashes("- - Two dashes") == 2
        assert parser._count_leading_dashes("- - - Three dashes") == 3

    def test_negative_context_for_other_codes(self):
        """'Other' codes without category should get negative context listing sibling categories."""
        mock_rows = [
            (None, None, None, None, None, None, None, None),
            (None, None, None, None, None, "4419", "Đồ dùng để bàn và đồ dùng nhà bếp, bằng gỗ", "Tableware and kitchenware, of wood"),
            (None, None, None, None, None, None, "- Từ tre:", "- Of bamboo:"),
            (None, None, None, None, None, "44191200", "- - Đũa", "- - Chopsticks"),
            (None, None, None, None, None, "44199000", "- Loại khác", "- Other"),
        ]

        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        other_code = next((hc for hc in hierarchy.hs_codes if hc.code == "44199000"), None)
        assert other_code is not None
        assert "không thuộc" in other_code.description_vn
        assert "Từ tre" in other_code.description_vn

        chopsticks = next((hc for hc in hierarchy.hs_codes if hc.code == "44191200"), None)
        assert chopsticks is not None
        assert "[Từ tre]" in chopsticks.description_vn


class TestNewColumnParsing:
    """Test cases for new HS code columns (TTDB, export duty, BVMT, VAT reduction)."""

    def _make_row_with_new_cols(
        self,
        code: str = "22030011",
        desc_vn: str = "- - Bia",
        desc_en: str = "- - Beer",
        ttdb: str | None = "65",
        export_duty: str | None = "0",
        bvmt: str | None = None,
        vat_reduction: str | None = None,
    ) -> tuple:
        """Build a row tuple with data in the right column positions."""
        # Build a row with enough columns to cover col 100
        row = [None] * 101
        row[5] = code
        row[6] = desc_vn
        row[7] = desc_en
        row[10] = 0  # duty_rate
        row[16] = 8  # vat_rate
        row[81] = ttdb  # special_consumption_tax
        row[84] = export_duty  # export_duty_rate
        row[96] = bvmt  # environmental_tax
        row[99] = None  # policy_notes
        row[100] = vat_reduction  # vat_reduction
        return tuple(row)

    def test_parse_ttdb(self):
        """TTDB (special consumption tax) should be parsed as string."""
        mock_rows = [
            tuple([None] * 8),
            self._make_row_with_new_cols(ttdb="65"),
        ]
        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        code = next((hc for hc in hierarchy.hs_codes if hc.code == "22030011"), None)
        assert code is not None
        assert code.special_consumption_tax == "65"

    def test_parse_ttdb_complex(self):
        """TTDB with complex values like '35/65' should be preserved as-is."""
        mock_rows = [
            tuple([None] * 8),
            self._make_row_with_new_cols(code="22042113", ttdb="35/65"),
        ]
        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        code = next((hc for hc in hierarchy.hs_codes if hc.code == "22042113"), None)
        assert code is not None
        assert code.special_consumption_tax == "35/65"

    def test_parse_export_duty(self):
        """Export duty rate should be parsed as string."""
        mock_rows = [
            tuple([None] * 8),
            self._make_row_with_new_cols(code="25020000", export_duty="10"),
        ]
        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        code = next((hc for hc in hierarchy.hs_codes if hc.code == "25020000"), None)
        assert code is not None
        assert code.export_duty_rate == "10"

    def test_parse_export_duty_complex(self):
        """Export duty with complex values like '10/10/30' should be preserved."""
        mock_rows = [
            tuple([None] * 8),
            self._make_row_with_new_cols(code="25051000", export_duty="10/10/30"),
        ]
        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        code = next((hc for hc in hierarchy.hs_codes if hc.code == "25051000"), None)
        assert code is not None
        assert code.export_duty_rate == "10/10/30"

    def test_parse_bvmt(self):
        """Environmental tax (BVMT) should be parsed as string."""
        mock_rows = [
            tuple([None] * 8),
            self._make_row_with_new_cols(code="27011100", bvmt="MT"),
        ]
        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        code = next((hc for hc in hierarchy.hs_codes if hc.code == "27011100"), None)
        assert code is not None
        assert code.environmental_tax == "MT"

    def test_parse_vat_reduction(self):
        """VAT reduction text should be parsed as string."""
        long_text = "Không được giảm VAT theo 174/2025/NĐ-CP"
        mock_rows = [
            tuple([None] * 8),
            self._make_row_with_new_cols(code="22021020", vat_reduction=long_text),
        ]
        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        code = next((hc for hc in hierarchy.hs_codes if hc.code == "22021020"), None)
        assert code is not None
        assert code.vat_reduction == long_text

    def test_empty_new_columns(self):
        """Empty/None new columns should result in None."""
        mock_rows = [
            tuple([None] * 8),
            self._make_row_with_new_cols(
                code="01012100",
                ttdb=None,
                export_duty=None,
                bvmt=None,
                vat_reduction=None,
            ),
        ]
        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        code = next((hc for hc in hierarchy.hs_codes if hc.code == "01012100"), None)
        assert code is not None
        assert code.special_consumption_tax is None
        assert code.export_duty_rate is None
        assert code.environmental_tax is None
        assert code.vat_reduction is None

    def test_whitespace_only_returns_none(self):
        """Whitespace-only values should be treated as None."""
        mock_rows = [
            tuple([None] * 8),
            self._make_row_with_new_cols(code="01012100", ttdb="  ", export_duty=""),
        ]
        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        code = next((hc for hc in hierarchy.hs_codes if hc.code == "01012100"), None)
        assert code is not None
        assert code.special_consumption_tax is None
        assert code.export_duty_rate is None


class TestFTAConditionsExtraction:
    """Test cases for extracting FTA conditions from rate cells."""

    def test_extract_conditions_simple(self):
        """Extract country exclusion from rate like '0(-MM)'."""
        parser = _make_parser()
        assert parser._extract_conditions("0(-MM)") == "-MM"

    def test_extract_conditions_multiple_countries(self):
        """Extract multiple country exclusions like '0(-KH, LA, MM, PH)'."""
        parser = _make_parser()
        result = parser._extract_conditions("0(-KH, LA, MM, PH)")
        assert result == "-KH, LA, MM, PH"

    def test_extract_conditions_with_space(self):
        """Handle space before parenthesis like '0 (-PH)'."""
        parser = _make_parser()
        assert parser._extract_conditions("0 (-PH)") == "-PH"

    def test_extract_conditions_none_for_numeric(self):
        """Numeric rate without conditions should return None."""
        parser = _make_parser()
        assert parser._extract_conditions("5.0") is None
        assert parser._extract_conditions(5.0) is None
        assert parser._extract_conditions(None) is None

    def test_fta_rate_includes_conditions(self):
        """FTA rates with parenthetical conditions should populate the conditions field."""
        # Header rows (rows 5-7) with legal_document and effective_date
        header_row_5 = [None] * 101
        header_row_6 = [None] * 101
        header_row_7 = [None] * 101
        header_row_6[32] = "108/2022/NĐ-CP"  # AKFTA legal_document at rate_col + 1
        header_row_6[33] = "30/12/2022"  # AKFTA effective_date at rate_col + 2

        # Data row
        row = [None] * 101
        row[5] = "01022911"
        row[6] = "- - - Test"
        row[7] = "- - - Test EN"
        row[10] = 0
        row[16] = 8
        row[31] = "0(-KR)"  # AKFTA rate with condition

        mock_rows = [
            tuple([None] * 8),  # rows 0-4
            tuple([None] * 8),
            tuple([None] * 8),
            tuple([None] * 8),
            tuple([None] * 8),
            tuple(header_row_5),  # row 5
            tuple(header_row_6),  # row 6 - has legal/effective date
            tuple(header_row_7),  # row 7
            tuple(row),  # data row
        ]
        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        code = next((hc for hc in hierarchy.hs_codes if hc.code == "01022911"), None)
        assert code is not None

        akfta_rate = next((r for r in code.fta_rates if r.agreement_code == "AKFTA"), None)
        assert akfta_rate is not None
        assert akfta_rate.conditions == "-KR"
        assert akfta_rate.legal_document == "108/2022/NĐ-CP"
        assert akfta_rate.effective_date == "30/12/2022"

    def test_fta_rate_no_conditions(self):
        """FTA rates without parenthetical conditions should have None conditions."""
        # Header rows with legal_document and effective_date
        header_row_5 = [None] * 101
        header_row_6 = [None] * 101
        header_row_7 = [None] * 101
        header_row_6[20] = "118/2022/NĐ-CP"  # ACFTA legal_document
        header_row_6[21] = "30/12/2022"  # ACFTA effective_date

        # Data row
        row = [None] * 101
        row[5] = "01012100"
        row[6] = "- Test"
        row[7] = "- Test EN"
        row[10] = 0
        row[16] = 8
        row[19] = 0  # ACFTA rate (plain numeric, no conditions)

        mock_rows = [
            tuple([None] * 8),
            tuple([None] * 8),
            tuple([None] * 8),
            tuple([None] * 8),
            tuple([None] * 8),
            tuple(header_row_5),
            tuple(header_row_6),
            tuple(header_row_7),
            tuple(row),
        ]
        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        code = next((hc for hc in hierarchy.hs_codes if hc.code == "01012100"), None)
        assert code is not None

        acfta_rate = next((r for r in code.fta_rates if r.agreement_code == "ACFTA"), None)
        assert acfta_rate is not None
        assert acfta_rate.conditions is None
        assert acfta_rate.legal_document == "118/2022/NĐ-CP"
        assert acfta_rate.effective_date == "30/12/2022"


class TestFTAHeaderParsing:
    """Test cases for parsing FTA legal_document and effective_date from header rows."""

    def test_parse_fta_headers(self):
        """Header rows should be parsed to extract legal_document and effective_date per FTA."""
        parser = _make_parser()

        # Mock rows with header data in rows 5-7
        header_row_5 = [None] * 101
        header_row_6 = [None] * 101
        header_row_7 = [None] * 101

        # ACFTA (rate_col=19): legal_document at col 20, effective_date at col 21
        header_row_6[20] = "118/2022/NĐ-CP"
        header_row_6[21] = "30/12/2022"

        # AKFTA (rate_col=31): legal_document at col 32, effective_date at col 33
        header_row_6[32] = "108/2022/NĐ-CP"
        header_row_7[33] = "15/01/2023"

        mock_rows = [
            tuple([None] * 8),
            tuple([None] * 8),
            tuple([None] * 8),
            tuple([None] * 8),
            tuple([None] * 8),
            tuple(header_row_5),
            tuple(header_row_6),
            tuple(header_row_7),
        ]

        metadata = parser._parse_fta_headers(mock_rows)

        assert "ACFTA" in metadata
        assert metadata["ACFTA"]["legal_document"] == "118/2022/NĐ-CP"
        assert metadata["ACFTA"]["effective_date"] == "30/12/2022"

        assert "AKFTA" in metadata
        assert metadata["AKFTA"]["legal_document"] == "108/2022/NĐ-CP"
        assert metadata["AKFTA"]["effective_date"] == "15/01/2023"

    def test_parse_fta_headers_missing_data(self):
        """FTAs without header metadata should have None values."""
        parser = _make_parser()

        # Mock rows with minimal header data
        mock_rows = [
            tuple([None] * 8),
            tuple([None] * 8),
            tuple([None] * 8),
            tuple([None] * 8),
            tuple([None] * 8),
            tuple([None] * 101),  # row 5
            tuple([None] * 101),  # row 6
            tuple([None] * 101),  # row 7
        ]

        metadata = parser._parse_fta_headers(mock_rows)

        # Should still have entries for all FTAs, but with None values
        assert "ACFTA" in metadata
        assert metadata["ACFTA"]["legal_document"] is None
        assert metadata["ACFTA"]["effective_date"] is None


class TestRCEPYearlyRates:
    """Test cases for RCEP yearly rate parsing (columns 71-75)."""

    def test_rcep_yearly_rates_parsed(self):
        """RCEP columns B-F (71-75) should be parsed as separate rate entries with year."""
        row = [None] * 101
        row[5] = "02011000"
        row[6] = "- Thịt bò"
        row[7] = "- Beef"
        row[10] = 20
        row[16] = 8
        row[70] = "15"  # RCEP A (base rate, imported as RCEPT with rate_year=NULL)
        row[71] = "15"  # RCEP B -> 2023
        row[72] = "15"  # RCEP C -> 2024
        row[73] = "16,4"  # RCEP D -> 2025 (uses comma as decimal separator)
        row[74] = "15"  # RCEP E -> 2026
        row[75] = "15"  # RCEP F -> 2027

        mock_rows = [tuple([None] * 8), tuple(row)]
        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        code = next((hc for hc in hierarchy.hs_codes if hc.code == "02011000"), None)
        assert code is not None

        rcep_rates = [r for r in code.fta_rates if r.agreement_code == "RCEPT"]
        # Should have 6 entries: base (NULL year) + 5 yearly (2023-2027)
        assert len(rcep_rates) == 6

        base = next((r for r in rcep_rates if r.rate_year is None), None)
        assert base is not None
        assert base.preferential_rate == Decimal("15")

        year_2025 = next((r for r in rcep_rates if r.rate_year == 2025), None)
        assert year_2025 is not None
        assert year_2025.preferential_rate == Decimal("16.4")

        year_2026 = next((r for r in rcep_rates if r.rate_year == 2026), None)
        assert year_2026 is not None
        assert year_2026.preferential_rate == Decimal("15")

    def test_rcep_base_rate_has_null_year(self):
        """The base RCEP rate (col 70) should have rate_year=None."""
        row = [None] * 101
        row[5] = "01012100"
        row[6] = "- Test"
        row[7] = "- Test EN"
        row[10] = 0
        row[16] = 0
        row[70] = 0  # RCEP A base rate

        mock_rows = [tuple([None] * 8), tuple(row)]
        parser = _make_parser()
        hierarchy = _run_parse(parser, mock_rows)

        code = next((hc for hc in hierarchy.hs_codes if hc.code == "01012100"), None)
        assert code is not None

        base_rcep = next(
            (r for r in code.fta_rates if r.agreement_code == "RCEPT" and r.rate_year is None),
            None
        )
        assert base_rcep is not None


class TestExportFTASheetParsing:
    """Test cases for export FTA sheet parsing."""

    def test_parse_export_fta_rates(self):
        """Export FTA rates should be parsed with is_export=True."""
        parser = _make_parser()
        parser.workbook = MagicMock()
        parser.workbook.sheetnames = ["CPTPP-XK", "EV-XK", "UKV-XK"]

        # Mock CPTPP-XK sheet
        cptpp_rows = [
            tuple([None] * 10),  # rows 0-5 = headers
            tuple([None] * 10),
            tuple([None] * 10),
            tuple([None] * 10),
            tuple([None] * 10),
            tuple([None] * 10),
            # row 6 = first data row (header_row=6)
            (None, "12119017", "Test desc", None, None, None, 9.5, None, None, None),
            (None, "1211901710", "Sub item", 9.5, 8.1, 6.8, 5.4, 4, 2.7, 1.3),
        ]

        ev_rows = [
            tuple([None] * 10),
            tuple([None] * 10),
            tuple([None] * 10),
            tuple([None] * 10),
            tuple([None] * 10),
            tuple([None] * 10),
            (None, None, "12112010", "Test", 0, 0, 0, 0, 0, 0),
        ]

        ukv_rows = [
            tuple([None] * 10),
            tuple([None] * 10),
            tuple([None] * 10),
            tuple([None] * 10),
            tuple([None] * 10),
            tuple([None] * 10),
            (None, "12112010", "Test", 0, 0, 0, 0, 0, 0, None),
        ]

        def get_sheet(self_mock, name):
            mock_sheet = MagicMock()
            if name == "CPTPP-XK":
                mock_sheet.iter_rows = MagicMock(return_value=iter(cptpp_rows))
            elif name == "EV-XK":
                mock_sheet.iter_rows = MagicMock(return_value=iter(ev_rows))
            elif name == "UKV-XK":
                mock_sheet.iter_rows = MagicMock(return_value=iter(ukv_rows))
            return mock_sheet

        parser.workbook.__getitem__ = get_sheet

        export_rates = parser.parse_export_fta_rates()

        # All export rates should have is_export=True
        for rate in export_rates:
            assert rate.is_export is True

        # Check CPTPP-XK rates
        cptpp_rates = [r for r in export_rates if r.agreement_code == "CPTPP-XK"]
        assert len(cptpp_rates) >= 1
        # 10-digit codes should be truncated to 8
        assert any(r.__dict__.get("_hs_code") == "12119017" for r in cptpp_rates)

    def test_missing_export_sheet_skipped(self):
        """Missing export sheets should be skipped with warning."""
        parser = _make_parser()
        parser.workbook = MagicMock()
        parser.workbook.sheetnames = []  # No sheets available

        export_rates = parser.parse_export_fta_rates()
        assert export_rates == []


class TestParseStringValue:
    """Test cases for _parse_string_value helper."""

    def test_none_returns_none(self):
        parser = _make_parser()
        assert parser._parse_string_value(None) is None

    def test_empty_string_returns_none(self):
        parser = _make_parser()
        assert parser._parse_string_value("") is None

    def test_whitespace_returns_none(self):
        parser = _make_parser()
        assert parser._parse_string_value("   ") is None

    def test_value_stripped(self):
        parser = _make_parser()
        assert parser._parse_string_value("  65  ") == "65"

    def test_numeric_converted_to_string(self):
        parser = _make_parser()
        assert parser._parse_string_value(65) == "65"


class TestFTARateDataDataclass:
    """Test FTARateData dataclass defaults."""

    def test_default_values(self):
        rate = FTARateData(agreement_code="ACFTA", preferential_rate=Decimal("5.0"))
        assert rate.conditions is None
        assert rate.rate_year is None
        assert rate.is_export is False
        assert rate.legal_document is None
        assert rate.effective_date is None

    def test_export_rate(self):
        rate = FTARateData(
            agreement_code="CPTPP-XK",
            preferential_rate=Decimal("2.7"),
            is_export=True,
        )
        assert rate.is_export is True
        assert rate.agreement_code == "CPTPP-XK"

    def test_yearly_rate(self):
        rate = FTARateData(
            agreement_code="RCEPT",
            preferential_rate=Decimal("15"),
            rate_year=2025,
        )
        assert rate.rate_year == 2025

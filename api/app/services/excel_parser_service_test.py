"""Tests for Excel parser service."""

from decimal import Decimal
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
from openpyxl import Workbook

from app.services.excel_parser_service import TariffExcelParser


def create_test_excel() -> Path:
    """Create a test Excel file with sample data."""
    wb = Workbook()
    ws = wb.active

    # Header row
    ws.append([
        "Mã HS",
        "Tên hàng hóa (Tiếng Việt)",
        "Product Name (English)",
        "Đơn vị tính",
        "Thuế suất nhập khẩu (%)",
        "VAT (%)",
        "CPTPP",
        "EVFTA",
        "RCEP",
        "Chú thích"
    ])

    # Sample data rows
    ws.append([
        "85094010",
        "Máy xay sinh tố gia đình",
        "Household food grinders and mixers",
        "Chiếc",
        20.0,
        10.0,
        0.0,
        5.0,
        10.0,
        "Test policy note"
    ])

    ws.append([
        "01234567",  # Code with leading zero
        "Hàng hóa test",
        "Test product",
        "Kg",
        15.5,
        10.0,
        "Miễn thuế",  # Duty-free text
        0.0,
        5.0,
        None
    ])

    ws.append([
        "99999999",
        "Sản phẩm khác",
        "Other product",
        None,  # No unit
        10.0,
        10.0,
        None,
        None,
        None,
        "Policy restriction"
    ])

    # Save to temporary file
    temp_file = NamedTemporaryFile(suffix=".xlsx", delete=False)
    wb.save(temp_file.name)
    temp_file.close()

    return Path(temp_file.name)


def test_parser_initialization():
    """Test parser initialization with Excel file."""
    excel_file = create_test_excel()
    try:
        parser = TariffExcelParser(excel_file)
        assert parser.file_path == excel_file
        assert parser.sheet is not None
        assert len(parser.column_mapping) > 0
        parser.close()
    finally:
        excel_file.unlink()


def test_parser_file_not_found():
    """Test parser raises error for non-existent file."""
    with pytest.raises(FileNotFoundError):
        TariffExcelParser("non_existent_file.xlsx")


def test_parse_all_hs_codes():
    """Test parsing all HS codes from Excel."""
    excel_file = create_test_excel()
    try:
        with TariffExcelParser(excel_file) as parser:
            hs_codes = parser.parse_all()

            # Should have 3 HS codes
            assert len(hs_codes) == 3

            # Check first HS code
            hs1 = hs_codes[0]
            assert hs1.code == "85094010"
            assert hs1.description_vn == "Máy xay sinh tố gia đình"
            assert hs1.description_en == "Household food grinders and mixers"
            assert hs1.unit == "Chiếc"
            assert hs1.duty_rate == Decimal("20.0")
            assert hs1.vat_rate == Decimal("10.0")
            assert hs1.policy_notes == "Test policy note"
            assert hs1.fta_rates["CPTPP"] == Decimal("0.0")
            assert hs1.fta_rates["EVFTA"] == Decimal("5.0")
            assert hs1.fta_rates["RCEP"] == Decimal("10.0")

            # Check second HS code (with leading zero)
            hs2 = hs_codes[1]
            assert hs2.code == "01234567"  # Leading zero preserved
            assert hs2.duty_rate == Decimal("15.5")  # Decimal precision
            assert hs2.fta_rates["CPTPP"] == Decimal("0.0")  # "Miễn thuế" converted to 0.0

            # Check third HS code (with None values)
            hs3 = hs_codes[2]
            assert hs3.code == "99999999"
            assert hs3.unit is None
            assert hs3.policy_notes == "Policy restriction"

    finally:
        excel_file.unlink()


def test_parse_code_preserves_leading_zeros():
    """Test that HS code format is preserved."""
    excel_file = create_test_excel()
    try:
        parser = TariffExcelParser(excel_file)

        # Test parsing codes with leading zeros
        assert parser._parse_code("01234567") == "01234567"
        assert parser._parse_code(1234567) == "01234567"  # Number gets padded
        assert parser._parse_code("12345678") == "12345678"

        parser.close()
    finally:
        excel_file.unlink()


def test_parse_rate_handles_various_formats():
    """Test parsing different rate formats."""
    excel_file = create_test_excel()
    try:
        parser = TariffExcelParser(excel_file)

        # Test various formats
        assert parser._parse_rate(20.0) == Decimal("20.0")
        assert parser._parse_rate("20%") == Decimal("20")
        assert parser._parse_rate("Miễn thuế") == Decimal("0.0")
        assert parser._parse_rate("FREE") == Decimal("0.0")
        assert parser._parse_rate(None) == Decimal("0.0")
        assert parser._parse_rate(15.50) == Decimal("15.50")

        parser.close()
    finally:
        excel_file.unlink()


def test_context_manager():
    """Test using parser as context manager."""
    excel_file = create_test_excel()
    try:
        with TariffExcelParser(excel_file) as parser:
            hs_codes = parser.parse_all()
            assert len(hs_codes) > 0
        # Workbook should be closed after context manager exits
    finally:
        excel_file.unlink()


def test_decimal_precision_preserved():
    """Test that decimal precision is preserved."""
    excel_file = create_test_excel()
    try:
        with TariffExcelParser(excel_file) as parser:
            hs_codes = parser.parse_all()

            # Find code with 15.5 duty rate
            hs = next(h for h in hs_codes if h.code == "01234567")
            assert hs.duty_rate == Decimal("15.5")
            assert float(hs.duty_rate) == 15.5

    finally:
        excel_file.unlink()

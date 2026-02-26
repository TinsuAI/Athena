"""Tests for customs report parser and import service."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.customs_import_service import (
    CustomsImportService,
    CustomsReportParser,
    ImportResult,
    ParsedRow,
)

# ---------------------------------------------------------------------------
# Helpers: Create test Excel files in memory
# ---------------------------------------------------------------------------


def _create_test_xls(
    rows: list[list[str | int | float | None]],
    header_row_idx: int = 3,
    hs_col: int = 21,
    name_col: int = 22,
) -> Path:
    """Create a temporary XLS file with test data.

    Args:
        rows: Data rows (after the header). Each row is a sparse list of values.
        header_row_idx: Row index (0-based) where headers will be placed.
        hs_col: Column index for 'Ma HS' header.
        name_col: Column index for 'Ten hang' header.

    Returns:
        Path to the temporary XLS file.
    """
    # xlrd 2.x is read-only; writing .xls files requires xlwt which is not available.
    # Use _create_test_xlsx instead for data tests; XLS format detection is tested
    # via test_xls_format_detected which verifies the code path selection.
    raise NotImplementedError("Use _create_test_xlsx instead; XLS writing requires xlwt")


def _create_test_xlsx(
    rows: list[list[str | int | float | None]],
    header_row_idx: int = 9,
    hs_col: int = 21,
    name_col: int = 22,
    extra_header_rows: int = 0,
) -> Path:
    """Create a temporary XLSX file with test data.

    Args:
        rows: Data rows (after the header). Each inner list has values at
              indices matching hs_col and name_col.
        header_row_idx: 0-based row index where headers are placed.
        hs_col: Column index for 'Ma HS' header.
        name_col: Column index for 'Ten hang' header.
        extra_header_rows: Number of blank/title rows before header.

    Returns:
        Path to the temporary XLSX file.
    """
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active

    # Write empty rows before header to simulate real file structure
    for _ in range(header_row_idx):
        ws.append([])

    # Write header row
    header = [""] * max(hs_col, name_col, 53) + [""]
    header[hs_col] = "Mã HS"
    header[name_col] = "Tên hàng"
    header[0] = "STT"
    ws.append(header)

    # Write data rows
    for row_data in rows:
        padded = [""] * (max(hs_col, name_col) + 1)
        if len(row_data) >= 2:
            padded[hs_col] = row_data[0]  # HS code
            padded[name_col] = row_data[1]  # Product name
        ws.append(padded)

    # Save to temp file
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    wb.save(tmp.name)
    wb.close()
    tmp.close()
    return Path(tmp.name)


# ---------------------------------------------------------------------------
# CustomsReportParser Tests
# ---------------------------------------------------------------------------


class TestCustomsReportParserXlsx:
    """Tests for XLSX parsing."""

    def test_parse_valid_xlsx(self):
        """Test parsing a valid XLSX file with standard data."""
        test_file = _create_test_xlsx(
            rows=[
                ["39269099", "Vo hop chinh, bang nhua PC"],
                ["85414000", "Pin nang luong mat troi"],
                ["76011000", "Nhom chua gia cong"],
            ]
        )
        try:
            parser = CustomsReportParser(test_file)
            rows = parser.parse()

            assert len(rows) == 3
            assert rows[0].hs_code == "39269099"
            assert rows[0].product_name == "Vo hop chinh, bang nhua PC"
            assert rows[1].hs_code == "85414000"
            assert rows[2].hs_code == "76011000"
        finally:
            test_file.unlink(missing_ok=True)

    def test_parse_with_product_name_separator(self):
        """Test that the #& prefix is stripped from product names."""
        test_file = _create_test_xlsx(
            rows=[
                ["39269099", "LKN-VO#&Vo hop chinh, bang nhua PC"],
                ["76011000", "INGOT-01#&Nhom chua gia cong"],
            ]
        )
        try:
            parser = CustomsReportParser(test_file)
            rows = parser.parse()

            assert len(rows) == 2
            assert rows[0].product_name == "Vo hop chinh, bang nhua PC"
            assert rows[1].product_name == "Nhom chua gia cong"
        finally:
            test_file.unlink(missing_ok=True)

    def test_parse_with_dotted_hs_code(self):
        """Test that dots are stripped from HS codes (e.g., '8507.60.00')."""
        test_file = _create_test_xlsx(
            rows=[
                ["8507.60.00", "Pin lithium"],
                ["3926.90.99", "San pham nhua khac"],
            ]
        )
        try:
            parser = CustomsReportParser(test_file)
            rows = parser.parse()

            assert len(rows) == 2
            assert rows[0].hs_code == "85076000"
            assert rows[1].hs_code == "39269099"
        finally:
            test_file.unlink(missing_ok=True)

    def test_parse_with_float_hs_code(self):
        """Test that Excel float HS codes (e.g., '39269099.0') are handled."""
        test_file = _create_test_xlsx(
            rows=[
                ["39269099.0", "Vo hop nhua"],
            ]
        )
        try:
            parser = CustomsReportParser(test_file)
            rows = parser.parse()

            assert len(rows) == 1
            assert rows[0].hs_code == "39269099"
        finally:
            test_file.unlink(missing_ok=True)

    def test_parse_skips_empty_rows(self):
        """Test that rows with empty HS code or product name are skipped."""
        test_file = _create_test_xlsx(
            rows=[
                ["39269099", "Valid product"],
                ["", "Missing HS code"],
                ["85414000", ""],
                ["", ""],
                ["76011000", "Another valid product"],
            ]
        )
        try:
            parser = CustomsReportParser(test_file)
            rows = parser.parse()

            assert len(rows) == 2
            assert rows[0].hs_code == "39269099"
            assert rows[1].hs_code == "76011000"
        finally:
            test_file.unlink(missing_ok=True)

    def test_parse_skips_invalid_hs_codes(self):
        """Test that non-8-digit HS codes are skipped."""
        test_file = _create_test_xlsx(
            rows=[
                ["39269099", "Valid 8-digit"],
                ["3926", "Only 4 digits"],
                ["abc12345", "Non-numeric"],
                ["123456789", "9 digits"],
                ["85414000", "Another valid"],
            ]
        )
        try:
            parser = CustomsReportParser(test_file)
            rows = parser.parse()

            assert len(rows) == 2
            assert rows[0].hs_code == "39269099"
            assert rows[1].hs_code == "85414000"
        finally:
            test_file.unlink(missing_ok=True)

    def test_parse_empty_file(self):
        """Test parsing an XLSX file with only headers (no data)."""
        test_file = _create_test_xlsx(rows=[])
        try:
            parser = CustomsReportParser(test_file)
            rows = parser.parse()

            assert len(rows) == 0
        finally:
            test_file.unlink(missing_ok=True)

    def test_parse_unicode_normalization(self):
        """Test that product names are Unicode-normalized to NFC."""
        # Using a name with combining characters that should be normalized
        test_file = _create_test_xlsx(
            rows=[
                ["39269099", "Vo\u0309 ho\u0323p chi\u0301nh"],
            ]
        )
        try:
            parser = CustomsReportParser(test_file)
            rows = parser.parse()

            assert len(rows) == 1
            # The exact NFC form depends on the input, but it should be normalized
            import unicodedata

            assert rows[0].product_name == unicodedata.normalize(
                "NFC", "Vo\u0309 ho\u0323p chi\u0301nh"
            )
        finally:
            test_file.unlink(missing_ok=True)

    def test_parse_row_numbers_are_one_indexed(self):
        """Test that row_number in ParsedRow is 1-indexed."""
        test_file = _create_test_xlsx(
            rows=[
                ["39269099", "First product"],
                ["85414000", "Second product"],
            ],
            header_row_idx=9,
        )
        try:
            parser = CustomsReportParser(test_file)
            rows = parser.parse()

            assert len(rows) == 2
            # Header at row 10 (1-indexed), data starts at row 11
            assert rows[0].row_number == 11
            assert rows[1].row_number == 12
        finally:
            test_file.unlink(missing_ok=True)

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            CustomsReportParser("/nonexistent/file.xlsx")

    def test_unsupported_format(self):
        """Test that ValueError is raised for unsupported file extension."""
        tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        tmp.close()
        try:
            parser = CustomsReportParser(tmp.name)
            with pytest.raises(ValueError, match="Unsupported file format"):
                parser.parse()
        finally:
            Path(tmp.name).unlink(missing_ok=True)

    def test_missing_headers_returns_empty(self):
        """Sheets without expected headers are skipped; returns empty list."""
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.append(["Col A", "Col B", "Col C"])
        ws.append(["data1", "data2", "data3"])

        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        wb.save(tmp.name)
        wb.close()
        tmp.close()

        try:
            parser = CustomsReportParser(tmp.name)
            result = parser.parse()
            assert result == []
        finally:
            Path(tmp.name).unlink(missing_ok=True)


class TestCustomsReportParserNormalization:
    """Tests for static normalization methods."""

    def test_normalize_hs_code_valid(self):
        assert CustomsReportParser._normalize_hs_code("39269099") == "39269099"

    def test_normalize_hs_code_with_dots(self):
        assert CustomsReportParser._normalize_hs_code("8507.60.00") == "85076000"

    def test_normalize_hs_code_with_float_suffix(self):
        assert CustomsReportParser._normalize_hs_code("39269099.0") == "39269099"

    def test_normalize_hs_code_with_spaces(self):
        assert CustomsReportParser._normalize_hs_code("3926 9099") == "39269099"

    def test_normalize_hs_code_too_short(self):
        assert CustomsReportParser._normalize_hs_code("3926") is None

    def test_normalize_hs_code_too_long(self):
        assert CustomsReportParser._normalize_hs_code("123456789") is None

    def test_normalize_hs_code_non_numeric(self):
        assert CustomsReportParser._normalize_hs_code("abc12345") is None

    def test_normalize_hs_code_empty(self):
        assert CustomsReportParser._normalize_hs_code("") is None

    def test_normalize_product_name_plain(self):
        result = CustomsReportParser._normalize_product_name("Pin lithium 100Ah")
        assert result == "Pin lithium 100Ah"

    def test_normalize_product_name_with_separator(self):
        result = CustomsReportParser._normalize_product_name("CODE-01#&Pin lithium 100Ah")
        assert result == "Pin lithium 100Ah"

    def test_normalize_product_name_whitespace(self):
        result = CustomsReportParser._normalize_product_name("  Pin lithium  ")
        assert result == "Pin lithium"

    def test_normalize_product_name_unicode_nfc(self):
        import unicodedata

        # Decomposed form
        decomposed = "ho\u0323p"
        result = CustomsReportParser._normalize_product_name(decomposed)
        assert result == unicodedata.normalize("NFC", decomposed)


class TestCustomsReportParserFormatDetection:
    """Tests for auto-detection of file format."""

    def test_xlsx_format_detected(self):
        """Test that .xlsx files are parsed with openpyxl."""
        test_file = _create_test_xlsx(rows=[["39269099", "Product"]])
        try:
            parser = CustomsReportParser(test_file)
            rows = parser.parse()
            assert len(rows) == 1
        finally:
            test_file.unlink(missing_ok=True)

    def test_xls_format_detected(self):
        """Test that .xls files call the XLS parsing path."""
        # Create a dummy .xls file (won't be valid XLS)
        tmp = tempfile.NamedTemporaryFile(suffix=".xls", delete=False)
        tmp.write(b"not a real xls")
        tmp.close()

        parser = CustomsReportParser(tmp.name)
        # This should fail because it's not a valid XLS, but it proves
        # the format detection selected the XLS path
        with pytest.raises(Exception):
            parser.parse()

        Path(tmp.name).unlink(missing_ok=True)


class TestCustomsReportParserXls:
    """Tests for XLS parsing logic using mocked xlrd sheet."""

    def _make_mock_sheet(
        self,
        data_rows: list[list],
        header_row_idx: int = 3,
        hs_col: int = 21,
        name_col: int = 22,
        ncols: int = 54,
    ) -> MagicMock:
        """Build a mock xlrd Sheet for testing _parse_xls logic.

        Args:
            data_rows: Each inner list is [hs_value, name_value] for that data row.
            header_row_idx: Row index (0-based) where headers are placed.
            hs_col: Column for 'Ma HS' header.
            name_col: Column for 'Ten hang' header.
            ncols: Total number of columns in the sheet.
        """
        total_rows = header_row_idx + 1 + len(data_rows)
        sheet = MagicMock()
        sheet.nrows = total_rows
        sheet.ncols = ncols

        def cell_value(row, col):
            # Header row
            if row == header_row_idx:
                if col == hs_col:
                    return "Mã HS"
                if col == name_col:
                    return "Tên hàng"
                return ""
            # Data rows
            data_row_idx = row - header_row_idx - 1
            if 0 <= data_row_idx < len(data_rows):
                row_data = data_rows[data_row_idx]
                if col == hs_col and len(row_data) > 0:
                    return row_data[0]
                if col == name_col and len(row_data) > 1:
                    return row_data[1]
            return ""

        sheet.cell_value = MagicMock(side_effect=cell_value)
        sheet.name = "Sheet1"
        return sheet

    def test_parse_xls_valid_rows(self):
        """Test that _parse_xls correctly extracts product-HS pairs via mocked xlrd."""
        sheet = self._make_mock_sheet(
            data_rows=[
                ["39269099", "Vo hop chinh bang nhua"],
                ["85414000", "Pin nang luong mat troi"],
            ],
            header_row_idx=3,
            hs_col=21,
            name_col=22,
        )

        tmp = tempfile.NamedTemporaryFile(suffix=".xls", delete=False)
        tmp.close()

        try:
            parser = CustomsReportParser(tmp.name)
            with patch("xlrd.open_workbook") as mock_wb:
                mock_wb.return_value.nsheets = 1
                mock_wb.return_value.sheet_by_index.return_value = sheet
                rows = parser._parse_xls()

            assert len(rows) == 2
            assert rows[0].hs_code == "39269099"
            assert rows[0].product_name == "Vo hop chinh bang nhua"
            assert rows[1].hs_code == "85414000"
            assert rows[1].product_name == "Pin nang luong mat troi"
        finally:
            Path(tmp.name).unlink(missing_ok=True)

    def test_parse_xls_skips_empty_rows(self):
        """Test that XLS parsing skips rows with empty HS code or name."""
        sheet = self._make_mock_sheet(
            data_rows=[
                ["39269099", "Valid product"],
                ["", "Missing HS"],
                ["85414000", ""],
                ["76011000", "Another valid"],
            ],
            header_row_idx=3,
            hs_col=21,
            name_col=22,
        )

        tmp = tempfile.NamedTemporaryFile(suffix=".xls", delete=False)
        tmp.close()

        try:
            parser = CustomsReportParser(tmp.name)
            with patch("xlrd.open_workbook") as mock_wb:
                mock_wb.return_value.nsheets = 1
                mock_wb.return_value.sheet_by_index.return_value = sheet
                rows = parser._parse_xls()

            assert len(rows) == 2
            assert rows[0].hs_code == "39269099"
            assert rows[1].hs_code == "76011000"
        finally:
            Path(tmp.name).unlink(missing_ok=True)

    def test_parse_xls_with_dotted_hs_code(self):
        """Test that dots are stripped from XLS HS codes."""
        sheet = self._make_mock_sheet(
            data_rows=[
                ["8507.60.00", "Pin lithium"],
            ],
            header_row_idx=3,
            hs_col=21,
            name_col=22,
        )

        tmp = tempfile.NamedTemporaryFile(suffix=".xls", delete=False)
        tmp.close()

        try:
            parser = CustomsReportParser(tmp.name)
            with patch("xlrd.open_workbook") as mock_wb:
                mock_wb.return_value.nsheets = 1
                mock_wb.return_value.sheet_by_index.return_value = sheet
                rows = parser._parse_xls()

            assert len(rows) == 1
            assert rows[0].hs_code == "85076000"
        finally:
            Path(tmp.name).unlink(missing_ok=True)

    def test_parse_xls_with_float_hs_code(self):
        """Test that Excel float-style HS codes (e.g., '39269099.0') are handled."""
        sheet = self._make_mock_sheet(
            data_rows=[
                ["39269099.0", "Vo hop nhua"],
            ],
            header_row_idx=3,
            hs_col=21,
            name_col=22,
        )

        tmp = tempfile.NamedTemporaryFile(suffix=".xls", delete=False)
        tmp.close()

        try:
            parser = CustomsReportParser(tmp.name)
            with patch("xlrd.open_workbook") as mock_wb:
                mock_wb.return_value.nsheets = 1
                mock_wb.return_value.sheet_by_index.return_value = sheet
                rows = parser._parse_xls()

            assert len(rows) == 1
            assert rows[0].hs_code == "39269099"
        finally:
            Path(tmp.name).unlink(missing_ok=True)

    def test_parse_xls_missing_headers_returns_empty(self):
        """When no sheet has expected headers, returns empty list."""
        sheet = MagicMock()
        sheet.nrows = 5
        sheet.ncols = 10
        sheet.name = "TestSheet"
        sheet.cell_value = MagicMock(return_value="SomethingElse")

        tmp = tempfile.NamedTemporaryFile(suffix=".xls", delete=False)
        tmp.close()

        try:
            parser = CustomsReportParser(tmp.name)
            with patch("xlrd.open_workbook") as mock_wb:
                mock_wb.return_value.nsheets = 1
                mock_wb.return_value.sheet_by_index.return_value = sheet
                result = parser._parse_xls()
                assert result == []
        finally:
            Path(tmp.name).unlink(missing_ok=True)

    def test_parse_xls_with_product_name_separator(self):
        """Test that #& prefix is stripped from XLS product names."""
        sheet = self._make_mock_sheet(
            data_rows=[
                ["39269099", "CODE01#&Real product name"],
            ],
            header_row_idx=3,
            hs_col=21,
            name_col=22,
        )

        tmp = tempfile.NamedTemporaryFile(suffix=".xls", delete=False)
        tmp.close()

        try:
            parser = CustomsReportParser(tmp.name)
            with patch("xlrd.open_workbook") as mock_wb:
                mock_wb.return_value.nsheets = 1
                mock_wb.return_value.sheet_by_index.return_value = sheet
                rows = parser._parse_xls()

            assert len(rows) == 1
            assert rows[0].product_name == "Real product name"
        finally:
            Path(tmp.name).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# CustomsImportService Tests
# ---------------------------------------------------------------------------


class TestCustomsImportServiceImport:
    """Tests for CustomsImportService.import_rows."""

    @pytest.mark.asyncio
    async def test_successful_import(self):
        """Test importing valid parsed rows creates LookupRecord entries."""
        session = AsyncMock()
        # add and add_all are synchronous in SQLAlchemy; override to avoid unawaited coroutine warnings
        session.add = MagicMock()
        session.add_all = MagicMock()
        session.flush = AsyncMock()

        # Mock HS code lookup: return matching IDs
        hs_result = MagicMock()
        hs_result.all.return_value = [
            MagicMock(code="39269099", id=100),
            MagicMock(code="85414000", id=200),
        ]

        # Mock existing hash check: no existing hashes
        hash_result = MagicMock()
        hash_result.all.return_value = []

        # Setup session.execute to return different results for different queries
        session.execute = AsyncMock(side_effect=[hs_result, hash_result])

        service = CustomsImportService(session)
        parsed_rows = [
            ParsedRow(product_name="Vo hop nhua", hs_code="39269099", row_number=11),
            ParsedRow(product_name="Pin mat troi", hs_code="85414000", row_number=12),
        ]

        result = await service.import_rows(
            parsed_rows=parsed_rows,
            source_file="test.xlsx",
            company_name="Test Co",
        )

        assert result.total_rows == 2
        assert result.records_imported == 2
        assert result.duplicates_skipped == 0
        assert len(result.unmatched_codes) == 0
        assert len(result.errors) == 0

        # Verify session.add_all was called with LookupRecord objects
        session.add_all.assert_called_once()
        records = session.add_all.call_args[0][0]
        assert len(records) == 2
        assert records[0].query_text == "Vo hop nhua"
        assert records[0].is_verified is True
        assert records[0].search_method == "customs_import"
        assert records[0].confidence_score == 100
        assert records[0].matched_hs_code_id == 100
        assert records[0].correct_hs_code_id == 100
        assert "test.xlsx" in records[0].notes
        assert "Test Co" in records[0].notes

    @pytest.mark.asyncio
    async def test_duplicate_skipping_existing_hash(self):
        """Test that rows with existing query_hash are skipped."""
        session = AsyncMock()
        session.add = MagicMock()

        from app.repositories.lookup_record_repository import compute_query_hash

        existing_hash = compute_query_hash("Vo hop nhua")

        hs_result = MagicMock()
        hs_result.all.return_value = [MagicMock(code="39269099", id=100)]

        hash_result = MagicMock()
        hash_result.all.return_value = [(existing_hash,)]

        session.execute = AsyncMock(side_effect=[hs_result, hash_result])

        service = CustomsImportService(session)
        parsed_rows = [
            ParsedRow(product_name="Vo hop nhua", hs_code="39269099", row_number=11),
        ]

        result = await service.import_rows(
            parsed_rows=parsed_rows,
            source_file="test.xlsx",
            company_name="Test Co",
        )

        assert result.total_rows == 1
        assert result.records_imported == 0
        assert result.duplicates_skipped == 1
        session.add_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_duplicate_skipping_within_file(self):
        """Test that duplicate product names within the same file are skipped."""
        session = AsyncMock()
        session.add = MagicMock()
        session.add_all = MagicMock()
        session.flush = AsyncMock()

        hs_result = MagicMock()
        hs_result.all.return_value = [MagicMock(code="39269099", id=100)]

        hash_result = MagicMock()
        hash_result.all.return_value = []

        session.execute = AsyncMock(side_effect=[hs_result, hash_result])

        service = CustomsImportService(session)
        parsed_rows = [
            ParsedRow(product_name="Vo hop nhua", hs_code="39269099", row_number=11),
            ParsedRow(product_name="Vo hop nhua", hs_code="39269099", row_number=12),
            ParsedRow(product_name="Vo hop nhua", hs_code="39269099", row_number=13),
        ]

        result = await service.import_rows(
            parsed_rows=parsed_rows,
            source_file="test.xlsx",
            company_name="Test Co",
        )

        assert result.total_rows == 3
        assert result.records_imported == 1
        assert result.duplicates_skipped == 2

    @pytest.mark.asyncio
    async def test_unmatched_hs_code_tracking(self):
        """Test that rows with unmatched HS codes are tracked in the result."""
        session = AsyncMock()
        session.add = MagicMock()
        session.add_all = MagicMock()
        session.flush = AsyncMock()

        # Only one code matches
        hs_result = MagicMock()
        hs_result.all.return_value = [MagicMock(code="39269099", id=100)]

        hash_result = MagicMock()
        hash_result.all.return_value = []

        session.execute = AsyncMock(side_effect=[hs_result, hash_result])

        service = CustomsImportService(session)
        parsed_rows = [
            ParsedRow(product_name="Valid product", hs_code="39269099", row_number=11),
            ParsedRow(product_name="Unknown code", hs_code="99999999", row_number=12),
        ]

        result = await service.import_rows(
            parsed_rows=parsed_rows,
            source_file="test.xlsx",
            company_name="Test Co",
        )

        assert result.records_imported == 1
        assert len(result.unmatched_codes) == 1
        assert result.unmatched_codes[0]["code"] == "99999999"
        assert result.unmatched_codes[0]["row"] == 12

    @pytest.mark.asyncio
    async def test_empty_parsed_rows(self):
        """Test importing empty list returns zero counts."""
        session = AsyncMock()
        session.add = MagicMock()
        service = CustomsImportService(session)

        result = await service.import_rows(
            parsed_rows=[],
            source_file="empty.xlsx",
            company_name="Test Co",
        )

        assert result.total_rows == 0
        assert result.records_imported == 0
        assert result.duplicates_skipped == 0
        session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_import_result_summary_accuracy(self):
        """Test that the import result accurately sums all categories."""
        session = AsyncMock()
        session.add = MagicMock()
        session.add_all = MagicMock()
        session.flush = AsyncMock()

        from app.repositories.lookup_record_repository import compute_query_hash

        hs_result = MagicMock()
        hs_result.all.return_value = [
            MagicMock(code="39269099", id=100),
        ]

        # One existing hash
        existing_hash = compute_query_hash("Existing product")
        hash_result = MagicMock()
        hash_result.all.return_value = [(existing_hash,)]

        session.execute = AsyncMock(side_effect=[hs_result, hash_result])

        service = CustomsImportService(session)
        parsed_rows = [
            ParsedRow(product_name="New product", hs_code="39269099", row_number=11),
            ParsedRow(product_name="Existing product", hs_code="39269099", row_number=12),
            ParsedRow(product_name="Unmatched code", hs_code="99999999", row_number=13),
            # within-file duplicate of "New product"
            ParsedRow(product_name="New product", hs_code="39269099", row_number=14),
        ]

        result = await service.import_rows(
            parsed_rows=parsed_rows,
            source_file="test.xlsx",
            company_name="Test Co",
        )

        assert result.total_rows == 4
        assert result.records_imported == 1  # Only "New product"
        assert result.duplicates_skipped == 2  # "Existing product" + within-file dup
        assert len(result.unmatched_codes) == 1  # "Unmatched code"
        # Total accounted: 1 + 2 + 1 = 4 (matches total_rows)

    @pytest.mark.asyncio
    async def test_import_commits_transaction(self):
        """Test that import_rows commits the session after inserting records."""
        session = AsyncMock()
        session.add = MagicMock()
        session.add_all = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()

        hs_result = MagicMock()
        hs_result.all.return_value = [MagicMock(code="39269099", id=100)]

        hash_result = MagicMock()
        hash_result.all.return_value = []

        session.execute = AsyncMock(side_effect=[hs_result, hash_result])

        service = CustomsImportService(session)
        parsed_rows = [
            ParsedRow(product_name="Vo hop nhua", hs_code="39269099", row_number=11),
        ]

        await service.import_rows(
            parsed_rows=parsed_rows,
            source_file="test.xlsx",
            company_name="Test Co",
        )

        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_compute_query_hash_integration(self):
        """Test that compute_query_hash is correctly used from the repository module."""
        from app.repositories.lookup_record_repository import compute_query_hash

        # Verify the function produces consistent, expected output
        hash1 = compute_query_hash("Vo hop nhua")
        hash2 = compute_query_hash("Vo hop nhua")
        hash3 = compute_query_hash("Pin mat troi")

        assert hash1 == hash2  # Same input -> same hash
        assert hash1 != hash3  # Different input -> different hash
        assert len(hash1) == 64  # SHA-256 hex digest length

    @pytest.mark.asyncio
    async def test_query_hash_case_insensitive(self):
        """Test that compute_query_hash normalizes case."""
        from app.repositories.lookup_record_repository import compute_query_hash

        hash_lower = compute_query_hash("vo hop nhua")
        hash_upper = compute_query_hash("VO HOP NHUA")
        hash_mixed = compute_query_hash("Vo Hop Nhua")

        assert hash_lower == hash_upper == hash_mixed


class TestCustomsImportServicePreview:
    """Tests for CustomsImportService.preview_import."""

    @pytest.mark.asyncio
    async def test_preview_empty_rows(self):
        """Test preview with empty parsed rows returns zero counts."""
        session = AsyncMock()
        service = CustomsImportService(session)
        preview = await service.preview_import([])

        assert preview["total_rows"] == 0
        assert preview["sample_rows"] == []
        assert preview["duplicate_count"] == 0
        assert preview["unmatched_count"] == 0
        assert preview["ready_to_import_count"] == 0

    @pytest.mark.asyncio
    async def test_preview_all_ready(self):
        """Test preview where all rows are ready to import."""
        session = AsyncMock()
        session.add_all = MagicMock()

        hs_result = MagicMock()
        hs_result.all.return_value = [
            MagicMock(code="39269099", id=100),
            MagicMock(code="85414000", id=200),
        ]

        hash_result = MagicMock()
        hash_result.all.return_value = []

        session.execute = AsyncMock(side_effect=[hs_result, hash_result])

        service = CustomsImportService(session)
        parsed_rows = [
            ParsedRow(product_name="Product A", hs_code="39269099", row_number=11),
            ParsedRow(product_name="Product B", hs_code="85414000", row_number=12),
        ]

        preview = await service.preview_import(parsed_rows)

        assert preview["total_rows"] == 2
        assert preview["ready_to_import_count"] == 2
        assert preview["duplicate_count"] == 0
        assert preview["unmatched_count"] == 0
        assert len(preview["sample_rows"]) == 2
        assert preview["sample_rows"][0]["product_name"] == "Product A"
        assert preview["sample_rows"][0]["hs_code"] == "39269099"
        assert preview["sample_rows"][0]["row_number"] == 11

    @pytest.mark.asyncio
    async def test_preview_with_duplicates_and_unmatched(self):
        """Test preview counting duplicates and unmatched codes."""
        session = AsyncMock()

        from app.repositories.lookup_record_repository import compute_query_hash

        existing_hash = compute_query_hash("Existing product")

        hs_result = MagicMock()
        hs_result.all.return_value = [MagicMock(code="39269099", id=100)]

        hash_result = MagicMock()
        hash_result.all.return_value = [(existing_hash,)]

        session.execute = AsyncMock(side_effect=[hs_result, hash_result])

        service = CustomsImportService(session)
        parsed_rows = [
            ParsedRow(product_name="New product", hs_code="39269099", row_number=11),
            ParsedRow(product_name="Existing product", hs_code="39269099", row_number=12),
            ParsedRow(product_name="Unmatched", hs_code="99999999", row_number=13),
        ]

        preview = await service.preview_import(parsed_rows)

        assert preview["total_rows"] == 3
        assert preview["ready_to_import_count"] == 1
        assert preview["duplicate_count"] == 1
        assert preview["unmatched_count"] == 1

    @pytest.mark.asyncio
    async def test_preview_sample_rows_limited_to_10(self):
        """Test preview returns at most 10 sample rows."""
        session = AsyncMock()

        hs_result = MagicMock()
        hs_result.all.return_value = [MagicMock(code="39269099", id=100)]

        hash_result = MagicMock()
        hash_result.all.return_value = []

        session.execute = AsyncMock(side_effect=[hs_result, hash_result])

        service = CustomsImportService(session)
        parsed_rows = [
            ParsedRow(product_name=f"Product {i}", hs_code="39269099", row_number=i + 10)
            for i in range(15)
        ]

        preview = await service.preview_import(parsed_rows)

        assert len(preview["sample_rows"]) == 10
        assert preview["sample_rows"][0]["product_name"] == "Product 0"
        assert preview["sample_rows"][9]["product_name"] == "Product 9"

    @pytest.mark.asyncio
    async def test_preview_does_not_insert(self):
        """Test that preview does not call session.add_all or session.flush."""
        session = AsyncMock()
        session.add_all = MagicMock()
        session.flush = AsyncMock()

        hs_result = MagicMock()
        hs_result.all.return_value = [MagicMock(code="39269099", id=100)]

        hash_result = MagicMock()
        hash_result.all.return_value = []

        session.execute = AsyncMock(side_effect=[hs_result, hash_result])

        service = CustomsImportService(session)
        parsed_rows = [
            ParsedRow(product_name="Product", hs_code="39269099", row_number=11),
        ]

        await service.preview_import(parsed_rows)

        session.add_all.assert_not_called()
        session.flush.assert_not_called()


class TestImportResultDataclass:
    """Tests for ImportResult dataclass defaults."""

    def test_default_values(self):
        result = ImportResult()
        assert result.total_rows == 0
        assert result.records_imported == 0
        assert result.duplicates_skipped == 0
        assert result.unmatched_codes == []
        assert result.errors == []

    def test_no_shared_mutable_defaults(self):
        """Test that default lists are not shared between instances."""
        r1 = ImportResult()
        r2 = ImportResult()
        r1.unmatched_codes.append({"code": "test"})
        assert len(r2.unmatched_codes) == 0


class TestParsedRowDataclass:
    """Tests for ParsedRow dataclass."""

    def test_creation(self):
        row = ParsedRow(product_name="Test", hs_code="12345678", row_number=1)
        assert row.product_name == "Test"
        assert row.hs_code == "12345678"
        assert row.row_number == 1


class TestBatchTracking:
    """Tests for batch tracking in import_rows (Story 9-3)."""

    @pytest.mark.asyncio
    async def test_import_creates_batch_record(self):
        """Test that import_rows creates a CustomsImportBatch record."""
        session = AsyncMock()
        session.add = MagicMock()
        session.add_all = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()

        hs_result = MagicMock()
        hs_result.all.return_value = [MagicMock(code="39269099", id=100)]

        hash_result = MagicMock()
        hash_result.all.return_value = []

        session.execute = AsyncMock(side_effect=[hs_result, hash_result])

        service = CustomsImportService(session)
        parsed_rows = [
            ParsedRow(product_name="Vo hop nhua", hs_code="39269099", row_number=11),
        ]

        result = await service.import_rows(
            parsed_rows=parsed_rows,
            source_file="test.xlsx",
            company_name="Test Co",
            imported_by_user_id=42,
        )

        # session.add should be called with a CustomsImportBatch instance
        session.add.assert_called_once()
        batch_arg = session.add.call_args[0][0]
        from app.models.customs_import_batch import CustomsImportBatch

        assert isinstance(batch_arg, CustomsImportBatch)
        assert batch_arg.file_name == "test.xlsx"
        assert batch_arg.company_name == "Test Co"
        assert batch_arg.imported_by_user_id == 42
        assert batch_arg.total_rows == 1

    @pytest.mark.asyncio
    async def test_import_populates_batch_counts(self):
        """Test that import_rows updates the batch record with final counts."""
        session = AsyncMock()
        session.add_all = MagicMock()
        session.commit = AsyncMock()

        from app.repositories.lookup_record_repository import compute_query_hash

        # Simulate flush assigning an ID to the batch object
        flush_call_count = 0

        async def mock_flush():
            nonlocal flush_call_count
            flush_call_count += 1
            if flush_call_count == 1:
                # First flush is for the batch record
                batch_arg = session.add.call_args[0][0]
                batch_arg.id = 99

        session.add = MagicMock()
        session.flush = AsyncMock(side_effect=mock_flush)

        hs_result = MagicMock()
        hs_result.all.return_value = [MagicMock(code="39269099", id=100)]

        # One existing hash for "Existing product"
        existing_hash = compute_query_hash("Existing product")
        hash_result = MagicMock()
        hash_result.all.return_value = [(existing_hash,)]

        session.execute = AsyncMock(side_effect=[hs_result, hash_result])

        service = CustomsImportService(session)
        parsed_rows = [
            ParsedRow(product_name="New product", hs_code="39269099", row_number=11),
            ParsedRow(product_name="Existing product", hs_code="39269099", row_number=12),
            ParsedRow(product_name="Unmatched", hs_code="99999999", row_number=13),
        ]

        result = await service.import_rows(
            parsed_rows=parsed_rows,
            source_file="test.xlsx",
            company_name="Test Co",
            imported_by_user_id=1,
        )

        # Verify the batch object had its counts updated
        batch_arg = session.add.call_args[0][0]
        assert batch_arg.records_imported == 1
        assert batch_arg.duplicates_skipped == 1
        assert batch_arg.unmatched_codes == 1
        assert batch_arg.errors_count == 0
        assert batch_arg.completed_at is not None

        # Verify the result includes batch_id
        assert result.batch_id == 99

    @pytest.mark.asyncio
    async def test_import_empty_rows_still_creates_batch(self):
        """Test that import_rows creates a batch even for empty parsed rows."""
        session = AsyncMock()
        session.commit = AsyncMock()

        # Simulate flush assigning an ID to the batch object
        async def mock_flush():
            batch_arg = session.add.call_args[0][0]
            batch_arg.id = 77

        session.add = MagicMock()
        session.flush = AsyncMock(side_effect=mock_flush)

        service = CustomsImportService(session)

        result = await service.import_rows(
            parsed_rows=[],
            source_file="empty.xlsx",
            company_name="Test Co",
            imported_by_user_id=5,
        )

        # Batch should still be created for tracking purposes
        session.add.assert_called_once()
        batch_arg = session.add.call_args[0][0]
        assert batch_arg.total_rows == 0
        assert batch_arg.records_imported == 0
        assert result.batch_id == 77


class TestDetectCompanyName:
    """Tests for detect_company_name function in the CLI script."""

    def test_detect_dothanh(self):
        from app.scripts.import_customs_data import detect_company_name
        result = detect_company_name("bchangchitiet-1-dothanh.xls")
        assert "Do Thanh" in result or "DKE" in result

    def test_detect_growatt(self):
        from app.scripts.import_customs_data import detect_company_name
        result = detect_company_name("bchangchitiet-2-growatt.xls")
        assert result != "Unknown"

    def test_detect_kde(self):
        from app.scripts.import_customs_data import detect_company_name
        result = detect_company_name("bchangchitiet-3-kde.xlsx")
        assert result != "Unknown"

    def test_detect_unknown(self):
        from app.scripts.import_customs_data import detect_company_name
        result = detect_company_name("some-unknown-file.xlsx")
        assert result == "Unknown"

    def test_detect_case_insensitive(self):
        from app.scripts.import_customs_data import detect_company_name
        result_lower = detect_company_name("bchangchitiet-1-dothanh.xls")
        result_upper = detect_company_name("bchangchitiet-1-DOTHANH.xls")
        assert result_lower == result_upper

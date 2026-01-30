"""Excel parser service for tariff data import."""

import logging
from decimal import Decimal
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

logger = logging.getLogger(__name__)


class HSCodeData:
    """Data class for parsed HS code."""

    def __init__(
        self,
        code: str,
        description_vn: str,
        description_en: str,
        unit: str | None,
        duty_rate: Decimal,
        vat_rate: Decimal,
        policy_notes: str | None,
        fta_rates: dict[str, Decimal],
    ):
        """Initialize HS code data."""
        self.code = code
        self.description_vn = description_vn
        self.description_en = description_en
        self.unit = unit
        self.duty_rate = duty_rate
        self.vat_rate = vat_rate
        self.policy_notes = policy_notes
        self.fta_rates = fta_rates  # dict of agreement_code -> rate

    def __repr__(self) -> str:
        """String representation."""
        return f"<HSCodeData(code='{self.code}', fta_rates={len(self.fta_rates)})>"


class TariffExcelParser:
    """Parser for Vietnam Customs tariff Excel files."""

    # FTA agreement codes we support - expanded list based on 2026 tariff schedule
    FTA_AGREEMENTS = [
        "ACFTA",
        "ATIGA",
        "AJCEP",
        "VJEPA",
        "AKFTA",
        "AANZFTA",
        "AIFTA",
        "VKFTA",
        "VCFTA",
        "VN-EAEU",
        "CPTPP",
        "AHKFTA",
        "VNCU",
        "EVFTA",
        "UKVFTA",
        "VN-LAO",
        "VIFTA",
        "RCEPT",  # Note: spelled RCEPT in the Excel file
    ]

    def __init__(self, file_path: str | Path):
        """Initialize parser with Excel file path."""
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.file_path}")

        self.workbook = load_workbook(filename=self.file_path, read_only=True, data_only=True)
        self.sheet: Worksheet = self.workbook.active  # type: ignore
        self.column_mapping: dict[str, int] = {}
        self._detect_columns()

    def _detect_columns(self) -> None:
        """Detect column positions from header row."""
        # Scan first 10 rows to find header row with "Mã hàng" (HS code column)
        header_row = None
        for row_idx in range(1, 10):
            row_values = [cell.value for cell in self.sheet[row_idx]]
            # Look for "Mã hàng" which is the HS code column header in 2026 tariff
            for idx, val in enumerate(row_values):
                if val and "MÃ HÀNG" in str(val).upper():
                    header_row = row_idx
                    break
            if header_row:
                break

        if not header_row:
            # Use fixed mapping for BIEU-THUE-XNK-2026.xlsx format
            # Based on actual file structure analysis
            logger.info("Using fixed column mapping for 2026 tariff format")
            self.column_mapping = {
                "code": 5,  # Column 6 (Mã hàng)
                "description_vn": 6,  # Column 7 (Mô tả hàng hoá - Tiếng Việt)
                "description_en": 7,  # Column 8 (Mô tả hàng hoá - Tiếng Anh)
                "unit": 8,  # Column 9 (Đơn vị tính)
                "duty_rate": 10,  # Column 11 (NK TT)
                "vat_rate": 16,  # Column 17 (VAT)
                "policy_notes": 99,  # Column 100 (Chính sách mặt hàng theo mã HS)
                # FTA agreements with their column indices (0-indexed)
                "fta_ACFTA": 19,
                "fta_ATIGA": 22,
                "fta_AJCEP": 25,
                "fta_VJEPA": 28,
                "fta_AKFTA": 31,
                "fta_AANZFTA": 34,
                "fta_AIFTA": 37,
                "fta_VKFTA": 40,
                "fta_VCFTA": 43,
                "fta_VN-EAEU": 46,
                "fta_CPTPP": 49,
                "fta_AHKFTA": 52,
                "fta_VNCU": 55,
                "fta_EVFTA": 58,
                "fta_UKVFTA": 61,
                "fta_VN-LAO": 64,
                "fta_VIFTA": 67,
                "fta_RCEPT": 70,
            }
            self.header_row = 3  # Row 3 contains headers
            return

        # Parse header row to map columns
        headers = [cell.value for cell in self.sheet[header_row]]
        self.header_row = header_row

        for idx, header in enumerate(headers):
            if not header:
                continue

            header_str = str(header).replace('\n', ' ')
            header_upper = header_str.upper()

            # Map standard columns
            if "MÃ HÀNG" in header_upper:
                self.column_mapping["code"] = idx
            elif "TIẾNG VIỆT" in header_upper:
                self.column_mapping["description_vn"] = idx
            elif "TIẾNG ANH" in header_upper or "ENGLISH" in header_upper:
                self.column_mapping["description_en"] = idx
            elif "ĐƠN VỊ" in header_upper and "TÍNH" in header_upper:
                self.column_mapping["unit"] = idx
            elif "NK" in header_upper and "TT" in header_upper:
                self.column_mapping["duty_rate"] = idx
            elif header_upper == "VAT":
                self.column_mapping["vat_rate"] = idx
            elif "CHÍNH SÁCH" in header_upper or "CHÚ THÍCH" in header_upper:
                self.column_mapping["policy_notes"] = idx

            # Map FTA columns - exact match to avoid matching "Văn bản" columns
            for agreement in self.FTA_AGREEMENTS:
                if header_upper == agreement or header_str == agreement:
                    self.column_mapping[f"fta_{agreement}"] = idx

        logger.info(f"Detected {len(self.column_mapping)} columns from header row {header_row}")

    def _parse_rate(self, value: Any, field_name: str = "rate", row_code: str = "") -> Decimal:
        """Parse a rate value from Excel cell.

        Args:
            value: The cell value to parse
            field_name: Name of the field being parsed (for error messages)
            row_code: HS code of the row being parsed (for error messages)

        Returns:
            Parsed rate as Decimal

        Raises:
            ValueError: If rate value cannot be parsed and is not a known exempt pattern
        """
        if value is None:
            return Decimal("0.00")

        # Handle string values
        if isinstance(value, str):
            value = value.strip()
            # Handle empty strings silently
            if not value:
                return Decimal("0.00")
            # Handle "Miễn thuế" (duty-free) - this is expected and valid
            if "MIỄN" in value.upper() or "FREE" in value.upper():
                return Decimal("0.00")
            # Handle "*" which means exempt or variable
            if value == "*":
                return Decimal("0.00")
            # Handle rates with country exclusions like "0(-MM)", "0(-LA)", "0(-KH,KR)"
            # Extract the leading number before parentheses
            if "(" in value:
                value = value.split("(")[0].strip()
                if not value:
                    return Decimal("0.00")
            # Handle rates with multiple conditions like "2.7;M:5.4" - take first value
            if ";" in value:
                value = value.split(";")[0].strip()
            # Handle complex VAT rates like "*/8/10" - take the last numeric value
            if "/" in value:
                parts = value.split("/")
                for part in reversed(parts):
                    part = part.strip().replace("%", "").replace("*", "")
                    # Handle European decimal format (comma)
                    part = part.replace(",", ".")
                    if part and (part.replace(".", "").isdigit() or (part.count(".") == 1 and part.replace(".", "").isdigit())):
                        try:
                            return Decimal(part)
                        except Exception:
                            pass
                # If no valid number found in slash-separated values, log warning
                logger.warning(
                    f"Complex rate format '{value}' for {field_name} "
                    f"(HS code: {row_code}), defaulting to 0.00"
                )
                return Decimal("0.00")
            # Remove % sign
            value = value.replace("%", "").strip()
            # Handle European decimal format (comma instead of dot)
            value = value.replace(",", ".")
            # Remove any whitespace
            value = value.replace(" ", "")

        try:
            parsed_value = Decimal(str(value))
            # Validate reasonable rate range (0-100%)
            if parsed_value < 0 or parsed_value > 200:
                logger.warning(
                    f"Suspicious rate value {parsed_value}% for {field_name} "
                    f"(HS code: {row_code}), but accepting as-is"
                )
            return parsed_value
        except Exception as e:
            # Critical: Cannot parse a rate value - log detailed error
            error_msg = (
                f"Failed to parse {field_name} value '{value}' "
                f"(HS code: {row_code}): {e}"
            )
            logger.error(error_msg)
            # For critical fields like duty_rate/vat_rate, raise exception
            if field_name in ("duty_rate", "vat_rate"):
                raise ValueError(error_msg)
            # For FTA rates, warn and default to 0.00 (less critical)
            logger.warning(f"Defaulting {field_name} to 0.00 for HS code {row_code}")
            return Decimal("0.00")

    def _parse_code(self, value: Any) -> str:
        """Parse HS code preserving format."""
        if value is None:
            return ""

        # Convert to string and preserve leading zeros
        code = str(value).strip()

        # Remove any dots or spaces
        code = code.replace(".", "").replace(" ", "")

        # Ensure 8 digits with leading zeros if needed
        if code.isdigit():
            code = code.zfill(8)

        return code

    def _get_row_value(self, row_data: list, col_name: str) -> Any:
        """Get value from row data by column name."""
        if col_name not in self.column_mapping:
            return None

        col_idx = self.column_mapping[col_name]
        if col_idx < len(row_data):
            return row_data[col_idx]
        return None

    def parse_all(self) -> list[HSCodeData]:
        """Parse all HS codes from the Excel file.

        Uses row iteration for efficiency in read_only mode.
        Deduplicates HS codes, keeping the first occurrence of each.
        """
        hs_codes: list[HSCodeData] = []
        seen_codes: set[str] = set()
        duplicate_count = 0
        start_row = self.header_row + 1
        row_count = 0

        logger.info(f"Starting to parse from row {start_row}, max_row={self.sheet.max_row}")

        # Iterate over rows efficiently (read_only mode optimized)
        for row in self.sheet.iter_rows(min_row=start_row, values_only=True):
            row_count += 1
            # Log row progress every 5000 rows
            if row_count % 5000 == 0:
                logger.info(f"Processing row {row_count}...")

            # Convert row tuple to list for easy indexing
            row_data = list(row) if row else []

            # Get HS code
            code = self._parse_code(self._get_row_value(row_data, "code"))

            # Skip empty rows or non-HS code rows
            if not code or len(code) != 8:
                continue

            # Skip invalid HS codes that start with "00" (these are likely chapter/heading codes)
            # Valid Vietnam HS codes start with 01-97 (chapters) or 98 (special provisions)
            if code.startswith("00"):
                continue

            # Skip duplicate codes (keep first occurrence)
            if code in seen_codes:
                duplicate_count += 1
                continue
            seen_codes.add(code)

            # Get descriptions
            description_vn = str(self._get_row_value(row_data, "description_vn") or "").strip()
            description_en = str(self._get_row_value(row_data, "description_en") or "").strip()

            # Skip if both descriptions are empty
            if not description_vn and not description_en:
                continue

            # Get other fields
            unit = self._get_row_value(row_data, "unit")
            if unit:
                unit = str(unit).strip()

            # Parse duty and VAT rates (critical fields - will raise on error)
            try:
                duty_rate = self._parse_rate(
                    self._get_row_value(row_data, "duty_rate"),
                    field_name="duty_rate",
                    row_code=code
                )
                vat_rate = self._parse_rate(
                    self._get_row_value(row_data, "vat_rate"),
                    field_name="vat_rate",
                    row_code=code
                )
            except ValueError as e:
                # Skip this row if critical rate parsing fails
                logger.error(f"Skipping HS code {code} due to rate parsing error: {e}")
                continue

            policy_notes = self._get_row_value(row_data, "policy_notes")
            if policy_notes:
                policy_notes = str(policy_notes).strip()

            # Parse FTA rates (non-critical - errors logged but not raised)
            fta_rates: dict[str, Decimal] = {}
            for agreement in self.FTA_AGREEMENTS:
                col_name = f"fta_{agreement}"
                rate_value = self._get_row_value(row_data, col_name)
                if rate_value is not None:
                    fta_rates[agreement] = self._parse_rate(
                        rate_value,
                        field_name=f"FTA_{agreement}",
                        row_code=code
                    )

            # Create HS code data
            hs_code_data = HSCodeData(
                code=code,
                description_vn=description_vn,
                description_en=description_en,
                unit=unit,
                duty_rate=duty_rate,
                vat_rate=vat_rate,
                policy_notes=policy_notes,
                fta_rates=fta_rates,
            )

            hs_codes.append(hs_code_data)

            # Log progress every 1000 records
            if len(hs_codes) % 1000 == 0:
                logger.info(f"Parsed {len(hs_codes)} unique HS codes...")

        logger.info(f"Completed parsing {len(hs_codes)} unique HS codes from {row_count} rows (skipped {duplicate_count} duplicates)")
        return hs_codes

    def close(self) -> None:
        """Close the workbook."""
        self.workbook.close()

    def __enter__(self) -> "TariffExcelParser":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

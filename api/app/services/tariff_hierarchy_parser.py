"""Tariff hierarchy parser for extracting sections, chapters, headings, and subheadings."""

import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

logger = logging.getLogger(__name__)


# Roman numeral conversion
ROMAN_TO_INT = {
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8,
    'IX': 9, 'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15,
    'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20, 'XXI': 21
}


@dataclass
class SectionData:
    """Data class for parsed HS section."""
    section_number: int
    section_roman: str
    name_vn: str
    name_en: str | None = None
    notes_vn: str | None = None
    notes_en: str | None = None


@dataclass
class ChapterData:
    """Data class for parsed HS chapter."""
    chapter_code: str  # "01", "02", etc.
    section_roman: str  # Parent section
    name_vn: str
    name_en: str | None = None
    notes_vn: str | None = None
    notes_en: str | None = None


@dataclass
class HeadingData:
    """Data class for parsed HS heading (4-digit)."""
    heading_code: str  # "0101", "0102", etc.
    chapter_code: str  # Parent chapter
    name_vn: str
    name_en: str | None = None


@dataclass
class SubheadingData:
    """Data class for parsed HS subheading (6-digit)."""
    subheading_code: str  # "010121", "010129", etc.
    heading_code: str  # Parent heading
    name_vn: str
    name_en: str | None = None
    indent_level: int = 0


@dataclass
class FTARateData:
    """Data class for a single FTA rate entry with metadata."""
    agreement_code: str
    preferential_rate: Decimal
    conditions: str | None = None
    rate_year: int | None = None
    is_export: bool = False
    legal_document: str | None = None
    effective_date: str | None = None

    def __repr__(self) -> str:
        """String representation."""
        return f"<FTARateData(agreement='{self.agreement_code}', rate={self.preferential_rate}, year={self.rate_year}, export={self.is_export})>"


@dataclass
class HSCodeData:
    """Data class for parsed HS code (8-digit)."""
    code: str
    subheading_code: str  # Parent subheading (first 6 digits)
    description_vn: str
    description_en: str
    unit: str | None = None
    duty_rate: Decimal = field(default_factory=lambda: Decimal("0.00"))
    vat_rate: Decimal = field(default_factory=lambda: Decimal("0.00"))
    export_duty_rate: str | None = None
    special_consumption_tax: str | None = None
    environmental_tax: str | None = None
    vat_reduction: str | None = None
    policy_notes: str | None = None
    fta_rates: list[FTARateData] = field(default_factory=list)
    indent_level: int = 0


@dataclass
class TariffHierarchy:
    """Complete tariff hierarchy data."""
    sections: list[SectionData] = field(default_factory=list)
    chapters: list[ChapterData] = field(default_factory=list)
    headings: list[HeadingData] = field(default_factory=list)
    subheadings: list[SubheadingData] = field(default_factory=list)
    hs_codes: list[HSCodeData] = field(default_factory=list)


class TariffHierarchyParser:
    """Parser for Vietnam Customs tariff Excel files with full hierarchy extraction."""

    # FTA agreement codes we support
    FTA_AGREEMENTS = [
        "ACFTA", "ATIGA", "AJCEP", "VJEPA", "AKFTA", "AANZFTA", "AIFTA",
        "VKFTA", "VCFTA", "VN-EAEU", "CPTPP", "AHKFTA", "VNCU", "EVFTA",
        "UKVFTA", "VN-LAO", "VIFTA", "RCEPT",
    ]

    # Fixed column mapping for 2026 tariff format
    # VERIFIED: Column indices confirmed against BIEU-THUE-XNK-2026.xlsx header row 7 on BT2026 sheet
    # Verification performed: 2026-02-11 during Story 2.1 implementation
    COLUMN_MAPPING: dict[str, int] = {
        "code": 5,  # Column F (Mã hàng)
        "description_vn": 6,  # Column G (Mô tả hàng hoá - Tiếng Việt)
        "description_en": 7,  # Column H (Mô tả hàng hoá - Tiếng Anh)
        "unit": 8,  # Column I (Đơn vị tính)
        "duty_rate": 10,  # Column K (NK TT)
        "vat_rate": 16,  # Column Q (VAT)
        "special_consumption_tax": 81,  # Column CD (TTDB) - VERIFIED
        "export_duty_rate": 84,  # Column CG (XK) - VERIFIED
        "environmental_tax": 96,  # Column CS (Thuế BVMT) - VERIFIED
        "policy_notes": 99,  # Column CV (Chính sách mặt hàng theo mã HS)
        "vat_reduction": 100,  # Column CW (Giảm VAT) - VERIFIED
        # FTA agreements — rate column index (0-indexed); +1 = legal_document, +2 = effective_date
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

    # RCEP sub-columns: schedules A-F mapped to years 2022-2027
    # Col 70 = A (2022, base rate imported as RCEPT with rate_year=NULL)
    # Cols 71-75 = B-F (2023-2027, imported with rate_year values)
    RCEP_YEARLY_COLUMNS: dict[int, int] = {
        71: 2023,  # B
        72: 2024,  # C
        73: 2025,  # D
        74: 2026,  # E
        75: 2027,  # F
    }

    # Export FTA sheet configurations: (sheet_name, agreement_code, code_col, rate_col)
    EXPORT_FTA_SHEETS: list[dict[str, Any]] = [
        {
            "sheet_name": "CPTPP-XK",
            "agreement_code": "CPTPP-XK",
            "code_col": 1,
            "rate_col": 6,  # Period (IV) ≈ 2026 for decree from 2022
            "header_row": 6,
        },
        {
            "sheet_name": "EV-XK",
            "agreement_code": "EV-XK",
            "code_col": 2,
            "rate_col": 8,  # Year 2026
            "header_row": 6,
        },
        {
            "sheet_name": "UKV-XK",
            "agreement_code": "UKV-XK",
            "code_col": 1,
            "rate_col": 7,  # Year 2026
            "header_row": 6,
        },
    ]

    def __init__(self, file_path: str | Path):
        """Initialize parser with Excel file path."""
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.file_path}")

        logger.info(f"Loading workbook: {self.file_path}")
        self.workbook = load_workbook(
            filename=self.file_path,
            read_only=True,
            data_only=True
        )
        self.sheet: Worksheet = self.workbook.active  # type: ignore
        logger.info(f"Workbook loaded, max rows: {self.sheet.max_row}")

    def _parse_rate(self, value: Any) -> Decimal:
        """Parse a rate value from Excel cell."""
        if value is None:
            return Decimal("0.00")

        if isinstance(value, str):
            value = value.strip()
            if not value:
                return Decimal("0.00")
            # Skip header values
            if value in ("Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"):
                return Decimal("0.00")
            if "MIỄN" in value.upper() or "FREE" in value.upper():
                return Decimal("0.00")
            if value == "*":
                return Decimal("0.00")
            # Skip complex text values that aren't rates
            if "thuế" in value.lower() or "MFN" in value:
                return Decimal("0.00")
            # Handle rates with country exclusions like "0(-MM)"
            if "(" in value:
                value = value.split("(")[0].strip()
                if not value:
                    return Decimal("0.00")
            # Handle rates with multiple conditions like "2.7;M:5.4"
            if ";" in value:
                value = value.split(";")[0].strip()
            # Handle complex VAT rates like "*/8/10"
            if "/" in value:
                parts = value.split("/")
                for part in reversed(parts):
                    part = part.strip().replace("%", "").replace("*", "").replace(",", ".")
                    if part and part.replace(".", "").isdigit():
                        try:
                            return Decimal(part)
                        except Exception:
                            pass
                return Decimal("0.00")
            value = value.replace("%", "").replace(",", ".").replace(" ", "")

        try:
            return Decimal(str(value))
        except Exception:
            # Silently ignore unparseable values
            return Decimal("0.00")

    def _parse_string_value(self, value: Any) -> str | None:
        """Parse a string value from Excel cell, returning None for empty/whitespace."""
        if value is None:
            return None
        s = str(value).strip()
        return s if s else None

    def _extract_conditions(self, value: Any) -> str | None:
        """Extract parenthetical conditions from a rate cell value like '0(-MM)' or '0 (-PH, MY)'.

        Note: This extracts only the FIRST set of parentheses. If multiple parenthetical
        expressions exist in a single cell, only the first is captured. This covers the
        vast majority of cases in the Excel file.
        """
        if value is None or not isinstance(value, str):
            return None
        match = re.search(r'\(([^)]+)\)', value)
        if match:
            return match.group(1).strip()
        return None

    def _parse_fta_headers(self, rows: list[tuple[Any, ...]]) -> dict[str, dict[str, str | None]]:
        """Parse FTA legal_document and effective_date from header rows 6-7.

        Returns a dict mapping agreement_code to {'legal_document': ..., 'effective_date': ...}
        These values are typically in header rows and apply to all HS codes for that FTA.
        """
        fta_metadata: dict[str, dict[str, str | None]] = {}

        # Check rows 5-7 (0-indexed) for header information
        header_rows = rows[5:8] if len(rows) > 7 else []

        for agreement in self.FTA_AGREEMENTS:
            rate_col = self.COLUMN_MAPPING.get(f"fta_{agreement}")
            if rate_col is None:
                continue

            legal_doc = None
            eff_date = None

            # Look in header rows for legal document and effective date
            # These are typically in columns rate_col+1 and rate_col+2 of header rows
            for header_row in header_rows:
                if len(header_row) > rate_col + 2:
                    # Check for legal document pattern (e.g., "108/2022/NĐ-CP")
                    col1_val = self._parse_string_value(header_row[rate_col + 1])
                    if col1_val and re.search(r'\d+/\d+', col1_val):
                        legal_doc = col1_val

                    # Check for date pattern (e.g., "30/12/2022")
                    col2_val = self._parse_string_value(header_row[rate_col + 2])
                    if col2_val and re.search(r'\d{1,2}/\d{1,2}/\d{4}', col2_val):
                        eff_date = col2_val

            fta_metadata[agreement] = {
                'legal_document': legal_doc,
                'effective_date': eff_date
            }

        return fta_metadata

    def _count_leading_dashes(self, text: str) -> int:
        """Count the number of leading dashes (indentation level)."""
        match = re.match(r'^(-\s*)+', text)
        if match:
            return text[:match.end()].count('-')
        return 0

    def _get_row_value(self, row: tuple[Any, ...], col_name: str) -> Any:
        """Get value from row data by column name."""
        col_idx = self.COLUMN_MAPPING.get(col_name)
        if col_idx is None:
            return None
        if col_idx < len(row):
            return row[col_idx]
        return None

    def _get_col_value(self, row: tuple[Any, ...], col_idx: int) -> Any:
        """Get value from row data by direct column index."""
        if col_idx < len(row):
            return row[col_idx]
        return None

    def parse_hierarchy(self) -> TariffHierarchy:
        """Parse the complete tariff hierarchy from the Excel file."""
        logger.info("Starting hierarchy extraction...")

        hierarchy = TariffHierarchy()
        rows = list(self.sheet.iter_rows(values_only=True))
        total_rows = len(rows)
        logger.info(f"Loaded {total_rows} rows into memory")

        # Parse FTA header metadata (legal_document, effective_date) from rows 6-7
        fta_metadata = self._parse_fta_headers(rows)
        logger.info(f"Parsed FTA header metadata for {len(fta_metadata)} agreements")

        # Current context for hierarchy tracking
        current_section: SectionData | None = None
        current_chapter: ChapterData | None = None
        current_heading: HeadingData | None = None
        current_subheading: SubheadingData | None = None

        # Track notes accumulation
        collecting_notes = False
        notes_buffer: list[str] = []

        # Track seen codes to avoid duplicates
        seen_headings: set[str] = set()
        seen_subheadings: set[str] = set()
        seen_hs_codes: set[str] = set()
        duplicate_count = 0

        # Category context tracking: [(indent_level, category_vn, category_en), ...]
        category_stack: list[tuple[int, str, str]] = []
        # Track all categories seen within current heading for negative context on "Other" codes
        heading_categories: list[tuple[str, str]] = []  # [(category_vn, category_en), ...]

        for row_idx, row in enumerate(rows):
            if row_idx % 5000 == 0:
                logger.info(f"Processing row {row_idx}/{total_rows}...")

            code_val = row[5] if len(row) > 5 else None
            desc_vn = row[6] if len(row) > 6 else None
            desc_en = row[7] if len(row) > 7 else None

            if not desc_vn:
                continue

            desc_vn_str = str(desc_vn).strip()
            desc_en_str = str(desc_en).strip() if desc_en else ""

            # Check for section (PHẦN I, PHẦN II, etc.)
            if desc_vn_str.startswith("PHẦN "):
                match = re.match(r"PHẦN\s+([IVXLCDM]+)", desc_vn_str)
                if match:
                    roman = match.group(1)
                    section_num = ROMAN_TO_INT.get(roman, 0)

                    # Get section name from next row
                    name_vn = ""
                    name_en = ""
                    if row_idx + 1 < len(rows):
                        next_row = rows[row_idx + 1]
                        name_vn = str(next_row[6]).strip() if len(next_row) > 6 and next_row[6] else ""
                        name_en = str(next_row[7]).strip() if len(next_row) > 7 and next_row[7] else ""

                    current_section = SectionData(
                        section_number=section_num,
                        section_roman=roman,
                        name_vn=name_vn,
                        name_en=name_en or None
                    )
                    hierarchy.sections.append(current_section)
                    logger.debug(f"Found section {roman}: {name_vn[:50]}...")

                    # Start collecting section notes
                    collecting_notes = True
                    notes_buffer = []
                continue

            # Check for chapter (Chương 1, Chương 2, etc.)
            if desc_vn_str.startswith("Chương "):
                # Skip note references like "Chương 72 không kể đến..."
                if "không kể đến" in desc_vn_str:
                    continue

                match = re.match(r"Chương\s+(\d+)", desc_vn_str)
                if match:
                    # Save notes to previous chapter if collecting
                    if collecting_notes and current_chapter and notes_buffer:
                        current_chapter.notes_vn = "\n".join(notes_buffer)
                    elif collecting_notes and current_section and notes_buffer:
                        current_section.notes_vn = "\n".join(notes_buffer)

                    chapter_num = match.group(1).zfill(2)

                    # Get chapter name from next row
                    name_vn = ""
                    name_en = ""
                    if row_idx + 1 < len(rows):
                        next_row = rows[row_idx + 1]
                        name_vn = str(next_row[6]).strip() if len(next_row) > 6 and next_row[6] else ""
                        name_en = str(next_row[7]).strip() if len(next_row) > 7 and next_row[7] else ""

                    current_chapter = ChapterData(
                        chapter_code=chapter_num,
                        section_roman=current_section.section_roman if current_section else "I",
                        name_vn=name_vn,
                        name_en=name_en or None
                    )
                    hierarchy.chapters.append(current_chapter)
                    logger.debug(f"Found chapter {chapter_num}: {name_vn[:50]}...")

                    # Start collecting chapter notes
                    collecting_notes = True
                    notes_buffer = []
                continue

            # Check for "Chú giải" (Notes section)
            if desc_vn_str == "Chú giải":
                collecting_notes = True
                notes_buffer = []
                continue

            # If collecting notes, accumulate until we hit a heading
            if collecting_notes and code_val is None:
                # Skip section/chapter names (all caps with many words)
                if not desc_vn_str.isupper() or len(desc_vn_str) < 10:
                    notes_buffer.append(desc_vn_str)
                continue

            # Calculate indent level for current row
            current_indent = self._count_leading_dashes(desc_vn_str)

            # Pop categories from stack when indent level decreases (moving to sibling or parent)
            while category_stack and category_stack[-1][0] >= current_indent:
                category_stack.pop()

            # Detect category indicator row: has description, no code, starts with dash
            if code_val is None and desc_vn_str.startswith("- "):
                # This is a category indicator - push to stack
                category_vn = desc_vn_str.lstrip("- ").rstrip(":").strip()
                category_en = desc_en_str.lstrip("- ").rstrip(":").strip() if desc_en_str else ""
                category_stack.append((current_indent, category_vn, category_en))
                # Also track for negative context on sibling "Other" codes
                heading_categories.append((category_vn, category_en))
                continue

            # Process code-based entries
            if code_val is None:
                continue

            code_str = str(code_val).strip().replace(".", "").replace(" ", "")

            # Stop collecting notes when we hit actual codes
            if collecting_notes and code_str:
                if current_chapter and notes_buffer:
                    current_chapter.notes_vn = "\n".join(notes_buffer)
                elif current_section and notes_buffer:
                    current_section.notes_vn = "\n".join(notes_buffer)
                collecting_notes = False
                notes_buffer = []

            # 4-digit code = Heading
            if len(code_str) == 4 and code_str.isdigit():
                # Clear category stack and heading categories when encountering a new heading
                category_stack.clear()
                heading_categories.clear()

                if code_str not in seen_headings:
                    seen_headings.add(code_str)
                    current_heading = HeadingData(
                        heading_code=code_str,
                        chapter_code=code_str[:2],
                        name_vn=desc_vn_str,
                        name_en=desc_en_str or None
                    )
                    hierarchy.headings.append(current_heading)
                current_subheading = None
                continue

            # 6-digit code = Subheading
            if len(code_str) == 6 and code_str.isdigit():
                if code_str not in seen_subheadings:
                    seen_subheadings.add(code_str)
                    indent = self._count_leading_dashes(desc_vn_str)
                    current_subheading = SubheadingData(
                        subheading_code=code_str,
                        heading_code=code_str[:4],
                        name_vn=desc_vn_str,
                        name_en=desc_en_str or None,
                        indent_level=indent
                    )
                    hierarchy.subheadings.append(current_subheading)
                continue

            # 8-digit code = HS Code (national tariff line)
            if len(code_str) == 8 and code_str.isdigit():
                # Skip invalid codes
                if code_str.startswith("00"):
                    continue

                # Skip duplicates
                if code_str in seen_hs_codes:
                    duplicate_count += 1
                    continue
                seen_hs_codes.add(code_str)

                # Determine subheading code
                subheading_code = code_str[:6]

                # Get codes for hierarchy
                heading_code = code_str[:4]
                chapter_code = code_str[:2]

                # Create virtual heading if it doesn't exist
                if heading_code not in seen_headings:
                    seen_headings.add(heading_code)
                    virtual_heading = HeadingData(
                        heading_code=heading_code,
                        chapter_code=chapter_code,
                        name_vn=desc_vn_str,
                        name_en=desc_en_str or None
                    )
                    hierarchy.headings.append(virtual_heading)

                # Create virtual subheading if it doesn't exist
                if subheading_code not in seen_subheadings:
                    seen_subheadings.add(subheading_code)
                    # Use the HS code's description for the virtual subheading
                    virtual_subheading = SubheadingData(
                        subheading_code=subheading_code,
                        heading_code=heading_code,
                        name_vn=desc_vn_str,
                        name_en=desc_en_str or None,
                        indent_level=self._count_leading_dashes(desc_vn_str)
                    )
                    hierarchy.subheadings.append(virtual_subheading)

                # Parse indent level
                indent = self._count_leading_dashes(desc_vn_str)

                # Parse rates
                duty_rate = self._parse_rate(self._get_row_value(row, "duty_rate"))
                vat_rate = self._parse_rate(self._get_row_value(row, "vat_rate"))

                # Parse unit
                unit = self._get_row_value(row, "unit")
                if unit:
                    unit = str(unit).strip()

                # Parse new tax/rate columns as strings (preserve original format)
                export_duty_rate = self._parse_string_value(self._get_row_value(row, "export_duty_rate"))
                special_consumption_tax = self._parse_string_value(
                    self._get_row_value(row, "special_consumption_tax")
                )
                environmental_tax = self._parse_string_value(self._get_row_value(row, "environmental_tax"))
                vat_reduction = self._parse_string_value(self._get_row_value(row, "vat_reduction"))

                # Parse policy notes
                policy_notes = self._get_row_value(row, "policy_notes")
                if policy_notes:
                    policy_notes = str(policy_notes).strip()

                # Parse FTA rates with conditions and metadata
                fta_rates: list[FTARateData] = []
                for agreement in self.FTA_AGREEMENTS:
                    rate_col = self.COLUMN_MAPPING.get(f"fta_{agreement}")
                    if rate_col is None:
                        continue
                    rate_value = self._get_col_value(row, rate_col)
                    if rate_value is None:
                        continue

                    # Extract conditions from rate value (e.g., "0(-MM)" -> "-MM")
                    conditions = self._extract_conditions(rate_value)

                    # Parse the numeric rate
                    parsed_rate = self._parse_rate(rate_value)

                    # Get legal_document and effective_date from header metadata
                    metadata = fta_metadata.get(agreement, {})
                    legal_doc = metadata.get('legal_document')
                    eff_date = metadata.get('effective_date')

                    fta_rates.append(FTARateData(
                        agreement_code=agreement,
                        preferential_rate=parsed_rate,
                        conditions=conditions,
                        legal_document=legal_doc,
                        effective_date=eff_date,
                    ))

                # Parse RCEP yearly rates (cols 71-75 = schedules B-F = years 2023-2027)
                for col_idx, year in self.RCEP_YEARLY_COLUMNS.items():
                    rcep_value = self._get_col_value(row, col_idx)
                    if rcep_value is None:
                        continue
                    parsed_rate = self._parse_rate(rcep_value)
                    fta_rates.append(FTARateData(
                        agreement_code="RCEPT",
                        preferential_rate=parsed_rate,
                        rate_year=year,
                    ))

                # Append category context from stack to description
                final_desc_vn = desc_vn_str
                final_desc_en = desc_en_str

                if category_stack:
                    # Build positive context string from stack
                    context_vn = " / ".join([c[1] for c in category_stack])
                    context_en = " / ".join([c[2] for c in category_stack if c[2]])

                    final_desc_vn = f"{desc_vn_str} [{context_vn}]"
                    if context_en:
                        final_desc_vn += f" [{context_en}]"
                elif heading_categories and "Loại khác" in desc_vn_str:
                    # Add negative context for "Other" codes that have sibling categories
                    # This helps search distinguish "Other bamboo" from "Other wood in general"
                    excluded_vn = ", ".join([c[0] for c in heading_categories])
                    excluded_en = ", ".join([c[1] for c in heading_categories if c[1]])

                    final_desc_vn = f"{desc_vn_str} [không thuộc: {excluded_vn}]"
                    if excluded_en:
                        final_desc_vn += f" [not: {excluded_en}]"

                hs_code = HSCodeData(
                    code=code_str,
                    subheading_code=subheading_code,
                    description_vn=final_desc_vn,
                    description_en=final_desc_en,
                    unit=unit,
                    duty_rate=duty_rate,
                    vat_rate=vat_rate,
                    export_duty_rate=export_duty_rate,
                    special_consumption_tax=special_consumption_tax,
                    environmental_tax=environmental_tax,
                    vat_reduction=vat_reduction,
                    policy_notes=policy_notes,
                    fta_rates=fta_rates,
                    indent_level=indent
                )
                hierarchy.hs_codes.append(hs_code)

                if len(hierarchy.hs_codes) % 1000 == 0:
                    logger.info(f"Parsed {len(hierarchy.hs_codes)} HS codes...")

        logger.info(f"Hierarchy extraction complete:")
        logger.info(f"  - Sections: {len(hierarchy.sections)}")
        logger.info(f"  - Chapters: {len(hierarchy.chapters)}")
        logger.info(f"  - Headings: {len(hierarchy.headings)}")
        logger.info(f"  - Subheadings: {len(hierarchy.subheadings)}")
        logger.info(f"  - HS Codes: {len(hierarchy.hs_codes)} (skipped {duplicate_count} duplicates)")

        return hierarchy

    def parse_export_fta_rates(self) -> list[FTARateData]:
        """Parse export FTA rates from CPTPP-XK, EV-XK, UKV-XK sheets.

        Returns a list of FTARateData entries with is_export=True.
        HS codes are stored as the agreement_code field temporarily;
        the import script maps them to hs_code_ids.

        Note: Currently only captures agreement_code, rate, and is_export flag.
        Conditions, legal_document, and effective_date from export sheet headers
        are not parsed in this version. This can be enhanced in future stories
        if export FTA metadata becomes required.
        """
        all_export_rates: list[FTARateData] = []

        for config in self.EXPORT_FTA_SHEETS:
            sheet_name = config["sheet_name"]
            if sheet_name not in self.workbook.sheetnames:
                logger.warning(f"Export FTA sheet '{sheet_name}' not found, skipping")
                continue

            sheet = self.workbook[sheet_name]
            rows = list(sheet.iter_rows(values_only=True))
            code_col = config["code_col"]
            rate_col = config["rate_col"]
            agreement = config["agreement_code"]
            header_row = config["header_row"]
            count = 0

            logger.info(f"Parsing export FTA sheet: {sheet_name} ({len(rows)} rows)")

            for row_idx, row in enumerate(rows):
                # Skip header rows
                if row_idx < header_row:
                    continue

                if code_col >= len(row):
                    continue

                code_val = row[code_col]
                if code_val is None:
                    continue

                code_str = str(code_val).strip().replace(".", "").replace(" ", "")

                # Only process 8-digit HS codes (skip 4-digit headings, 6-digit subheadings, 10-digit)
                if len(code_str) == 10:
                    code_str = code_str[:8]
                if len(code_str) != 8 or not code_str.isdigit():
                    continue

                rate_value = row[rate_col] if rate_col < len(row) else None
                parsed_rate = self._parse_rate(rate_value)

                # Store code in a way the import script can use to match hs_code_id
                # We repurpose a temporary attribute by creating a custom object
                rate_data = FTARateData(
                    agreement_code=agreement,
                    preferential_rate=parsed_rate,
                    is_export=True,
                )
                # Attach hs_code string for matching (stored via __dict__ to avoid dataclass field)
                rate_data.__dict__["_hs_code"] = code_str
                all_export_rates.append(rate_data)
                count += 1

            logger.info(f"  Parsed {count} export FTA rates from {sheet_name}")

        logger.info(f"Total export FTA rates parsed: {len(all_export_rates)}")
        return all_export_rates

    def close(self) -> None:
        """Close the workbook."""
        self.workbook.close()

    def __enter__(self) -> "TariffHierarchyParser":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

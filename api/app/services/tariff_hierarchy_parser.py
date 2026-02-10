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
class HSCodeData:
    """Data class for parsed HS code (8-digit)."""
    code: str
    subheading_code: str  # Parent subheading (first 6 digits)
    description_vn: str
    description_en: str
    unit: str | None = None
    duty_rate: Decimal = field(default_factory=lambda: Decimal("0.00"))
    vat_rate: Decimal = field(default_factory=lambda: Decimal("0.00"))
    policy_notes: str | None = None
    fta_rates: dict[str, Decimal] = field(default_factory=dict)
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
    COLUMN_MAPPING = {
        "code": 5,  # Column F (Mã hàng)
        "description_vn": 6,  # Column G (Mô tả hàng hoá - Tiếng Việt)
        "description_en": 7,  # Column H (Mô tả hàng hoá - Tiếng Anh)
        "unit": 8,  # Column I (Đơn vị tính)
        "duty_rate": 10,  # Column K (NK TT)
        "vat_rate": 16,  # Column Q (VAT)
        "policy_notes": 99,  # Column CV (Chính sách mặt hàng theo mã HS)
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

    def _count_leading_dashes(self, text: str) -> int:
        """Count the number of leading dashes (indentation level)."""
        match = re.match(r'^(-\s*)+', text)
        if match:
            return text[:match.end()].count('-')
        return 0

    def _get_row_value(self, row: tuple, col_name: str) -> Any:
        """Get value from row data by column name."""
        col_idx = self.COLUMN_MAPPING.get(col_name)
        if col_idx is None:
            return None
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

                # Parse policy notes
                policy_notes = self._get_row_value(row, "policy_notes")
                if policy_notes:
                    policy_notes = str(policy_notes).strip()

                # Parse FTA rates
                fta_rates: dict[str, Decimal] = {}
                for agreement in self.FTA_AGREEMENTS:
                    rate_value = self._get_row_value(row, f"fta_{agreement}")
                    if rate_value is not None:
                        fta_rates[agreement] = self._parse_rate(rate_value)

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

    def close(self) -> None:
        """Close the workbook."""
        self.workbook.close()

    def __enter__(self) -> "TariffHierarchyParser":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

"""Pydantic schemas for tariff browse API responses."""

from pydantic import BaseModel, Field


class BrowseSectionItem(BaseModel):
    """Section list item with computed chapter count."""

    id: int = Field(description="Section ID")
    section_number: int = Field(description="Section number (1-21)")
    section_roman: str = Field(description="Roman numeral (I, II, III, etc.)")
    name_vn: str = Field(description="Vietnamese name")
    name_en: str | None = Field(default=None, description="English name")
    chapter_count: int = Field(description="Number of chapters in this section")

    model_config = {"from_attributes": True}


class BrowseChapterItem(BaseModel):
    """Chapter list item with computed counts."""

    id: int = Field(description="Chapter ID")
    chapter_code: str = Field(description="2-digit chapter code")
    name_vn: str = Field(description="Vietnamese name")
    name_en: str | None = Field(default=None, description="English name")
    heading_count: int = Field(description="Number of headings in this chapter")
    hs_code_count: int = Field(description="Number of HS codes in this chapter")

    model_config = {"from_attributes": True}


class BrowseChaptersResponse(BaseModel):
    """Chapters list with section notes."""

    section_notes_vn: str | None = Field(default=None, description="Section notes in Vietnamese")
    section_notes_en: str | None = Field(default=None, description="Section notes in English")
    chapters: list[BrowseChapterItem] = Field(description="Chapters in this section")


class BrowseFTARateItem(BaseModel):
    """FTA rate with all fields for browse display."""

    agreement_code: str = Field(description="FTA agreement code")
    preferential_rate: float = Field(description="Preferential tariff rate (%)")
    conditions: str | None = Field(default=None, description="Eligibility conditions")
    rate_year: int | None = Field(default=None, description="Rate year")
    is_export: bool = Field(description="Whether this is an export FTA rate")
    legal_document: str | None = Field(default=None, description="Legal document reference")
    effective_date: str | None = Field(default=None, description="Effective date")

    model_config = {"from_attributes": True}


class BrowseHSCodeItem(BaseModel):
    """HS code with full rate data and nested FTA rates."""

    id: int = Field(description="HS code ID")
    code: str = Field(description="8-digit HS code")
    description_vn: str = Field(description="Vietnamese description")
    description_en: str = Field(description="English description")
    unit: str | None = Field(default=None, description="Unit of measure")
    duty_rate: float = Field(description="Standard import duty rate (%)")
    vat_rate: float = Field(description="VAT rate (%)")
    export_duty_rate: str | None = Field(default=None, description="Export duty rate")
    special_consumption_tax: str | None = Field(default=None, description="Special consumption tax")
    environmental_tax: str | None = Field(default=None, description="Environmental tax")
    vat_reduction: str | None = Field(default=None, description="VAT reduction info")
    policy_notes: str | None = Field(default=None, description="Policy notes")
    fta_rates: list[BrowseFTARateItem] = Field(default_factory=list, description="FTA rates")

    model_config = {"from_attributes": True}


class BrowseSubheadingItem(BaseModel):
    """Subheading with nested HS codes."""

    id: int = Field(description="Subheading ID")
    subheading_code: str = Field(description="6-digit subheading code")
    name_vn: str = Field(description="Vietnamese name")
    name_en: str | None = Field(default=None, description="English name")
    indent_level: int | None = Field(default=None, description="Indent level")
    hs_codes: list[BrowseHSCodeItem] = Field(default_factory=list, description="HS codes")

    model_config = {"from_attributes": True}


class BrowseHeadingItem(BaseModel):
    """Heading with nested subheadings."""

    id: int = Field(description="Heading ID")
    heading_code: str = Field(description="4-digit heading code")
    name_vn: str = Field(description="Vietnamese name")
    name_en: str | None = Field(default=None, description="English name")
    subheadings: list[BrowseSubheadingItem] = Field(default_factory=list, description="Subheadings")

    model_config = {"from_attributes": True}


class BrowseChapterDetailResponse(BaseModel):
    """Full chapter hierarchy with notes."""

    id: int = Field(description="Chapter ID")
    chapter_code: str = Field(description="2-digit chapter code")
    name_vn: str = Field(description="Vietnamese name")
    name_en: str | None = Field(default=None, description="English name")
    notes_vn: str | None = Field(default=None, description="Chapter notes in Vietnamese")
    notes_en: str | None = Field(default=None, description="Chapter notes in English")
    headings: list[BrowseHeadingItem] = Field(default_factory=list, description="Headings")

    model_config = {"from_attributes": True}


class BrowseSearchResultItem(BaseModel):
    """Search result with hierarchy path and inline rates."""

    id: int = Field(description="HS code ID")
    code: str = Field(description="8-digit HS code")
    description_vn: str = Field(description="Vietnamese description")
    description_en: str = Field(description="English description")
    unit: str | None = Field(default=None, description="Unit of measure")
    duty_rate: float = Field(description="Standard import duty rate (%)")
    vat_rate: float = Field(description="VAT rate (%)")
    export_duty_rate: str | None = Field(default=None, description="Export duty rate")
    section_roman: str = Field(description="Section roman numeral")
    chapter_code: str = Field(description="2-digit chapter code")
    heading_code: str = Field(description="4-digit heading code")

    model_config = {"from_attributes": True}


class PaginatedBrowseSearchResponse(BaseModel):
    """Paginated search results."""

    items: list[BrowseSearchResultItem] = Field(description="Search result items")
    total: int = Field(description="Total number of matching results")
    limit: int = Field(description="Page size")
    offset: int = Field(description="Page offset")

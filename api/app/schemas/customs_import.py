"""Pydantic schemas for customs data import API responses."""

from pydantic import BaseModel, Field


class SampleRow(BaseModel):
    """A single sample row from the customs report preview."""

    product_name: str = Field(description="Product description from the customs report")
    hs_code: str = Field(description="HS code (8-digit)")
    row_number: int = Field(description="Original row number in the uploaded file")


class CustomsImportPreviewResponse(BaseModel):
    """Preview data returned after parsing an uploaded customs report file."""

    file_name: str = Field(description="Original uploaded filename")
    total_rows: int = Field(description="Total parseable rows found in the file")
    sample_rows: list[SampleRow] = Field(
        description="First 10 rows for preview"
    )
    duplicate_count: int = Field(
        description="Rows already existing in the knowledge base"
    )
    unmatched_count: int = Field(
        description="Rows with HS codes not found in the database"
    )
    ready_to_import_count: int = Field(
        description="Rows ready to be imported (new + matched)"
    )


class CustomsImportResultResponse(BaseModel):
    """Result data returned after executing a customs report import."""

    file_name: str = Field(description="Original uploaded filename")
    total_rows: int = Field(description="Total rows processed")
    records_imported: int = Field(description="Successfully imported records")
    duplicates_skipped: int = Field(description="Skipped duplicate records")
    unmatched_codes: list[dict] = Field(
        default_factory=list,
        description="HS codes not found in the database",
    )
    errors: list[dict] = Field(
        default_factory=list,
        description="Rows that caused errors during import",
    )
    elapsed_seconds: float = Field(description="Time taken for the import in seconds")

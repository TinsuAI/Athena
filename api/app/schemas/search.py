"""Pydantic schemas for search API."""

from pydantic import BaseModel, Field


class ProcessLogEntry(BaseModel):
    """A single log entry from search processing."""

    step: str = Field(description="Step name (e.g., 'enhancement', 'search', 'reranking')")
    status: str = Field(description="Status: 'started', 'completed', 'failed', 'skipped'")
    message: str = Field(description="Human-readable message")
    duration_ms: int | None = Field(default=None, description="Duration in milliseconds")
    details: dict | None = Field(default=None, description="Additional details (e.g., enhanced query, candidates)")


class SearchRequest(BaseModel):
    """Search request body."""

    query: str = Field(
        min_length=1,
        max_length=500,
        description="Search query - product description or HS code"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return"
    )
    model: str | None = Field(
        default=None,
        max_length=100,
        description="LLM model to use for classification reasoning (e.g., 'openai/gpt-4o-mini')"
    )


class ClassificationSchema(BaseModel):
    """Classification analysis schema."""

    material: str = Field(description="Material classification reasoning")
    function: str = Field(description="Function/purpose classification reasoning")


class SearchResultSchema(BaseModel):
    """Single search result with classification analysis."""

    hs_code: str = Field(description="8-digit HS code")
    description: str = Field(description="Vietnamese description of the HS code")
    duty_rate: str = Field(description="Import duty rate (formatted)")
    vat_rate: str = Field(description="VAT rate (formatted)")
    classification: ClassificationSchema = Field(description="Classification reasoning")
    practical_notes: list[str] = Field(description="Practical import notes")
    confidence: int = Field(ge=0, le=100, description="Match confidence percentage")


class SearchResponseData(BaseModel):
    """Search response data - the best matching result."""

    hs_code: str = Field(description="8-digit HS code (formatted with dots)")
    description: str = Field(description="Vietnamese description")
    duty_rate: str = Field(description="Import duty rate (formatted with %)")
    vat_rate: str = Field(description="VAT rate (formatted with %)")
    classification: ClassificationSchema = Field(description="Classification reasoning")
    practical_notes: list[str] = Field(description="Practical import notes")
    confidence: int = Field(ge=0, le=100, description="Match confidence (0-100%)")
    process_logs: list[ProcessLogEntry] = Field(default_factory=list, description="Detailed process logs")

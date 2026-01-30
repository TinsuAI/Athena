"""Pydantic schemas for HS code API responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class FTARateSchema(BaseModel):
    """Schema for FTA rate data."""

    id: int = Field(description="FTA rate ID")
    agreement_code: str = Field(description="FTA agreement code (e.g., CPTPP, EVFTA)")
    preferential_rate: float = Field(description="Preferential tariff rate (%)")
    conditions: str | None = Field(default=None, description="Eligibility conditions")
    created_at: datetime = Field(description="Creation timestamp")

    model_config = {"from_attributes": True}


class HSCodeSchema(BaseModel):
    """Schema for HS code data."""

    id: int = Field(description="HS code ID")
    code: str = Field(description="8-digit HS code")
    description_vn: str = Field(description="Vietnamese description")
    description_en: str = Field(description="English description")
    unit: str | None = Field(default=None, description="Unit of measure")
    duty_rate: float = Field(description="Standard import duty rate (%)")
    vat_rate: float = Field(description="VAT rate (%)")
    policy_notes: str | None = Field(default=None, description="Policy restrictions/notes")
    data_version_id: int = Field(description="Data version ID")
    created_at: datetime = Field(description="Creation timestamp")
    fta_rates: list[FTARateSchema] = Field(default_factory=list, description="FTA preferential rates")

    model_config = {"from_attributes": True}


class HSCodeResponseData(BaseModel):
    """Response data wrapper for HS code endpoint."""

    hs_code: HSCodeSchema = Field(description="HS code with FTA rates")

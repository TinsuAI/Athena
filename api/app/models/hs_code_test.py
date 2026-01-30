"""Tests for HS code models."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_version import DataVersion
from app.models.fta_rate import FTARate
from app.models.hs_code import HSCode


@pytest.mark.asyncio
async def test_create_hs_code_with_relationships(db_session: AsyncSession):
    """Test creating an HS code with data version and FTA rates."""
    # Create data version
    data_version = DataVersion(
        name="2026 Tariff Schedule",
        source_file="BIEU-THUE-XNK-2026.xlsx",
        is_active=True
    )
    db_session.add(data_version)
    await db_session.flush()

    # Create HS code
    hs_code = HSCode(
        code="85094010",
        description_vn="Máy xay sinh tố gia đình",
        description_en="Household food grinders and mixers",
        unit="Chiếc",
        duty_rate=20.0,
        vat_rate=10.0,
        policy_notes="Test policy notes",
        data_version_id=data_version.id
    )
    db_session.add(hs_code)
    await db_session.flush()

    # Create FTA rates
    fta_rate_1 = FTARate(
        hs_code_id=hs_code.id,
        agreement_code="CPTPP",
        preferential_rate=0.0,
        conditions="C/O required"
    )
    fta_rate_2 = FTARate(
        hs_code_id=hs_code.id,
        agreement_code="EVFTA",
        preferential_rate=5.0,
        conditions="EUR.1 certificate"
    )
    db_session.add_all([fta_rate_1, fta_rate_2])
    await db_session.commit()

    # Verify relationships
    result = await db_session.execute(
        select(HSCode).where(HSCode.code == "85094010")
    )
    retrieved_hs_code = result.scalar_one()

    assert retrieved_hs_code.code == "85094010"
    assert retrieved_hs_code.description_vn == "Máy xay sinh tố gia đình"
    assert retrieved_hs_code.duty_rate == 20.0
    assert retrieved_hs_code.vat_rate == 10.0
    assert retrieved_hs_code.data_version_id == data_version.id


@pytest.mark.asyncio
async def test_hs_code_unique_constraint(db_session: AsyncSession):
    """Test that HS code must be unique."""
    data_version = DataVersion(
        name="Test Version",
        source_file="test.xlsx",
        is_active=True
    )
    db_session.add(data_version)
    await db_session.flush()

    hs_code_1 = HSCode(
        code="12345678",
        description_vn="Test VN",
        description_en="Test EN",
        unit="Test",
        duty_rate=10.0,
        vat_rate=10.0,
        data_version_id=data_version.id
    )
    db_session.add(hs_code_1)
    await db_session.commit()

    # Try to create duplicate
    hs_code_2 = HSCode(
        code="12345678",
        description_vn="Different VN",
        description_en="Different EN",
        unit="Different",
        duty_rate=15.0,
        vat_rate=10.0,
        data_version_id=data_version.id
    )
    db_session.add(hs_code_2)

    with pytest.raises(Exception):  # Will be IntegrityError
        await db_session.commit()


@pytest.mark.asyncio
async def test_hs_code_preserves_format(db_session: AsyncSession):
    """Test that HS code format is preserved (no truncation)."""
    data_version = DataVersion(
        name="Test Version",
        source_file="test.xlsx",
        is_active=True
    )
    db_session.add(data_version)
    await db_session.flush()

    # Test with leading zeros
    hs_code = HSCode(
        code="01234567",
        description_vn="Test",
        description_en="Test",
        unit="Test",
        duty_rate=10.0,
        vat_rate=10.0,
        data_version_id=data_version.id
    )
    db_session.add(hs_code)
    await db_session.commit()

    result = await db_session.execute(
        select(HSCode).where(HSCode.code == "01234567")
    )
    retrieved = result.scalar_one()

    # Verify leading zeros preserved
    assert retrieved.code == "01234567"
    assert len(retrieved.code) == 8


@pytest.mark.asyncio
async def test_decimal_precision_preserved(db_session: AsyncSession):
    """Test that decimal precision is preserved for rates."""
    data_version = DataVersion(
        name="Test Version",
        source_file="test.xlsx",
        is_active=True
    )
    db_session.add(data_version)
    await db_session.flush()

    hs_code = HSCode(
        code="12345678",
        description_vn="Test",
        description_en="Test",
        unit="Test",
        duty_rate=20.00,  # Precise decimal
        vat_rate=10.50,   # Precise decimal
        data_version_id=data_version.id
    )
    db_session.add(hs_code)
    await db_session.commit()

    result = await db_session.execute(
        select(HSCode).where(HSCode.code == "12345678")
    )
    retrieved = result.scalar_one()

    # Verify decimal precision
    assert float(retrieved.duty_rate) == 20.00
    assert float(retrieved.vat_rate) == 10.50


@pytest.mark.asyncio
async def test_fta_rate_cascade_delete(db_session: AsyncSession):
    """Test that FTA rates are deleted when HS code is deleted."""
    data_version = DataVersion(
        name="Test Version",
        source_file="test.xlsx",
        is_active=True
    )
    db_session.add(data_version)
    await db_session.flush()

    hs_code = HSCode(
        code="99999999",
        description_vn="Test",
        description_en="Test",
        unit="Test",
        duty_rate=10.0,
        vat_rate=10.0,
        data_version_id=data_version.id
    )
    db_session.add(hs_code)
    await db_session.flush()

    fta_rate = FTARate(
        hs_code_id=hs_code.id,
        agreement_code="TEST",
        preferential_rate=0.0,
        conditions="Test"
    )
    db_session.add(fta_rate)
    await db_session.commit()

    # Delete HS code
    await db_session.delete(hs_code)
    await db_session.commit()

    # Verify FTA rate was also deleted
    result = await db_session.execute(
        select(FTARate).where(FTARate.hs_code_id == hs_code.id)
    )
    assert result.scalar_one_or_none() is None

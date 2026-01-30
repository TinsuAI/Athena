"""Tests for HS code repository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_version import DataVersion
from app.models.fta_rate import FTARate
from app.models.hs_code import HSCode
from app.repositories.hs_code_repository import HSCodeRepository


@pytest.mark.asyncio
async def test_get_by_code(db_session: AsyncSession):
    """Test getting an HS code by its code."""
    # Create test data
    data_version = DataVersion(
        name="Test Version",
        source_file="test.xlsx",
        is_active=True
    )
    db_session.add(data_version)
    await db_session.flush()

    hs_code = HSCode(
        code="12345678",
        description_vn="Test VN",
        description_en="Test EN",
        unit="Test",
        duty_rate=10.0,
        vat_rate=10.0,
        data_version_id=data_version.id
    )
    db_session.add(hs_code)
    await db_session.commit()

    # Test repository
    repo = HSCodeRepository(db_session)
    result = await repo.get_by_code("12345678")

    assert result is not None
    assert result.code == "12345678"
    assert result.description_vn == "Test VN"


@pytest.mark.asyncio
async def test_get_by_code_not_found(db_session: AsyncSession):
    """Test getting non-existent HS code returns None."""
    repo = HSCodeRepository(db_session)
    result = await repo.get_by_code("99999999")

    assert result is None


@pytest.mark.asyncio
async def test_get_with_fta_rates(db_session: AsyncSession):
    """Test getting HS code with FTA rates eagerly loaded."""
    # Create test data
    data_version = DataVersion(
        name="Test Version",
        source_file="test.xlsx",
        is_active=True
    )
    db_session.add(data_version)
    await db_session.flush()

    hs_code = HSCode(
        code="85094010",
        description_vn="Test Product",
        description_en="Test Product",
        unit="Piece",
        duty_rate=20.0,
        vat_rate=10.0,
        data_version_id=data_version.id
    )
    db_session.add(hs_code)
    await db_session.flush()

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

    # Test repository
    repo = HSCodeRepository(db_session)
    result = await repo.get_with_fta_rates("85094010")

    assert result is not None
    assert result.code == "85094010"
    assert len(result.fta_rates) == 2
    assert result.fta_rates[0].agreement_code in ("CPTPP", "EVFTA")
    assert result.fta_rates[1].agreement_code in ("CPTPP", "EVFTA")


@pytest.mark.asyncio
async def test_count_all(db_session: AsyncSession):
    """Test counting all HS codes."""
    # Create test data
    data_version = DataVersion(
        name="Test Version",
        source_file="test.xlsx",
        is_active=True
    )
    db_session.add(data_version)
    await db_session.flush()

    for i in range(5):
        hs_code = HSCode(
            code=f"1234567{i}",
            description_vn=f"Test {i}",
            description_en=f"Test {i}",
            unit="Test",
            duty_rate=10.0,
            vat_rate=10.0,
            data_version_id=data_version.id
        )
        db_session.add(hs_code)

    await db_session.commit()

    # Test repository
    repo = HSCodeRepository(db_session)
    count = await repo.count_all()

    assert count == 5


@pytest.mark.asyncio
async def test_get_all(db_session: AsyncSession):
    """Test getting all HS codes with pagination."""
    # Create test data
    data_version = DataVersion(
        name="Test Version",
        source_file="test.xlsx",
        is_active=True
    )
    db_session.add(data_version)
    await db_session.flush()

    for i in range(15):
        hs_code = HSCode(
            code=f"10{i:06d}",  # Ensure 8 digits total
            description_vn=f"Test {i}",
            description_en=f"Test {i}",
            unit="Test",
            duty_rate=10.0,
            vat_rate=10.0,
            data_version_id=data_version.id
        )
        db_session.add(hs_code)

    await db_session.commit()

    # Test repository
    repo = HSCodeRepository(db_session)

    # Get first page
    result = await repo.get_all(limit=10, offset=0)
    assert len(result) == 10

    # Get second page
    result = await repo.get_all(limit=10, offset=10)
    assert len(result) == 5


@pytest.mark.asyncio
async def test_search_by_description(db_session: AsyncSession):
    """Test searching HS codes by description."""
    # Create test data
    data_version = DataVersion(
        name="Test Version",
        source_file="test.xlsx",
        is_active=True
    )
    db_session.add(data_version)
    await db_session.flush()

    hs_code_1 = HSCode(
        code="12345678",
        description_vn="Máy xay sinh tố",
        description_en="Food grinder",
        unit="Piece",
        duty_rate=10.0,
        vat_rate=10.0,
        data_version_id=data_version.id
    )
    hs_code_2 = HSCode(
        code="87654321",
        description_vn="Xe ô tô",
        description_en="Automobile",
        unit="Unit",
        duty_rate=20.0,
        vat_rate=10.0,
        data_version_id=data_version.id
    )
    db_session.add_all([hs_code_1, hs_code_2])
    await db_session.commit()

    # Test repository
    repo = HSCodeRepository(db_session)

    # Search Vietnamese
    result = await repo.search_by_description("sinh tố", language="vn")
    assert len(result) == 1
    assert result[0].code == "12345678"

    # Search English
    result = await repo.search_by_description("grinder", language="en")
    assert len(result) == 1
    assert result[0].code == "12345678"

    # Search both languages
    result = await repo.search_by_description("automobile", language="both")
    assert len(result) == 1
    assert result[0].code == "87654321"

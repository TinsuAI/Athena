"""Tests for HS codes API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.models.data_version import DataVersion
from app.models.fta_rate import FTARate
from app.models.hs_code import HSCode


@pytest.mark.asyncio
async def test_get_hs_code_success(db_session: AsyncSession):
    """Test successfully getting an HS code."""
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

    fta_rate = FTARate(
        hs_code_id=hs_code.id,
        agreement_code="CPTPP",
        preferential_rate=0.0,
        conditions="C/O required"
    )
    db_session.add(fta_rate)
    await db_session.commit()

    # Make API request
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/hs-codes/85094010")

    # Verify response
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["error"] is None
    assert data["data"] is not None

    # Note: Envelope format - HS code data is directly in 'data' (no wrapper)
    hs_code_data = data["data"]
    assert hs_code_data["code"] == "85094010"
    assert hs_code_data["description_vn"] == "Máy xay sinh tố gia đình"
    assert hs_code_data["description_en"] == "Household food grinders and mixers"
    assert hs_code_data["duty_rate"] == 20.0
    assert hs_code_data["vat_rate"] == 10.0
    assert len(hs_code_data["fta_rates"]) == 1
    assert hs_code_data["fta_rates"][0]["agreement_code"] == "CPTPP"


@pytest.mark.asyncio
async def test_get_hs_code_not_found():
    """Test getting non-existent HS code returns 404."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/hs-codes/99999999")

    assert response.status_code == 200  # Envelope format always returns 200

    data = response.json()
    assert data["success"] is False
    assert data["data"] is None
    assert data["error"] is not None
    assert data["error"]["status"] == 404
    assert data["error"]["title"] == "Not Found"
    assert "99999999" in data["error"]["detail"]


@pytest.mark.asyncio
async def test_get_hs_code_invalid_format():
    """Test getting HS code with invalid format returns 400."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/hs-codes/INVALID")

    assert response.status_code == 200  # Envelope format always returns 200

    data = response.json()
    assert data["success"] is False
    assert data["data"] is None
    assert data["error"] is not None
    assert data["error"]["status"] == 400
    assert data["error"]["title"] == "Invalid HS Code Format"


@pytest.mark.asyncio
async def test_get_hs_code_with_multiple_fta_rates(db_session: AsyncSession):
    """Test getting HS code with multiple FTA rates."""
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
        description_vn="Test Product",
        description_en="Test Product",
        unit="Piece",
        duty_rate=15.0,
        vat_rate=10.0,
        data_version_id=data_version.id
    )
    db_session.add(hs_code)
    await db_session.flush()

    # Add multiple FTA rates
    fta_rates = [
        FTARate(
            hs_code_id=hs_code.id,
            agreement_code="CPTPP",
            preferential_rate=0.0
        ),
        FTARate(
            hs_code_id=hs_code.id,
            agreement_code="EVFTA",
            preferential_rate=5.0
        ),
        FTARate(
            hs_code_id=hs_code.id,
            agreement_code="RCEP",
            preferential_rate=10.0
        ),
    ]
    db_session.add_all(fta_rates)
    await db_session.commit()

    # Make API request
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/hs-codes/12345678")

    # Verify response
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    # Envelope format - HS code data is directly in 'data' (no wrapper)
    hs_code_data = data["data"]
    assert len(hs_code_data["fta_rates"]) == 3

    # Verify all FTA agreements are present
    agreement_codes = {rate["agreement_code"] for rate in hs_code_data["fta_rates"]}
    assert agreement_codes == {"CPTPP", "EVFTA", "RCEP"}


# --- Autocomplete endpoint tests (Story 1-10, Task 3) ---


class TestAutocompleteHSCodes:
    """Test GET /api/hs-codes/autocomplete endpoint."""

    def _make_mock_hs_code(self, **kwargs):
        """Create a mock HSCode object."""
        defaults = {
            "id": 1,
            "code": "74182000",
            "description_vn": "Bộ đồ bàn nhà bếp",
            "description_en": "Kitchen table set",
        }
        defaults.update(kwargs)
        mock = MagicMock()
        for key, value in defaults.items():
            setattr(mock, key, value)
        return mock

    @pytest.mark.asyncio
    @patch("app.api.hs_codes.HSCodeService")
    async def test_returns_results(self, mock_service_class):
        """Test autocomplete returns matching results."""
        from app.api.hs_codes import autocomplete_hs_codes

        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        mock_service.autocomplete.return_value = [
            self._make_mock_hs_code(id=1, code="74182000"),
            self._make_mock_hs_code(id=2, code="74183000"),
        ]

        mock_db = AsyncMock()
        result = await autocomplete_hs_codes(q="7418", limit=10, db=mock_db)

        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["code"] == "74182000"
        assert result["data"][1]["code"] == "74183000"

    @pytest.mark.asyncio
    @patch("app.api.hs_codes.HSCodeService")
    async def test_empty_query_returns_empty(self, mock_service_class):
        """Test empty query returns empty list without calling service."""
        from app.api.hs_codes import autocomplete_hs_codes

        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        mock_db = AsyncMock()
        result = await autocomplete_hs_codes(q="", limit=10, db=mock_db)

        assert result["success"] is True
        assert result["data"] == []
        mock_service.autocomplete.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("app.api.hs_codes.HSCodeService")
    async def test_whitespace_query_returns_empty(self, mock_service_class):
        """Test whitespace-only query returns empty list."""
        from app.api.hs_codes import autocomplete_hs_codes

        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        mock_db = AsyncMock()
        result = await autocomplete_hs_codes(q="   ", limit=10, db=mock_db)

        assert result["success"] is True
        assert result["data"] == []

    @pytest.mark.asyncio
    @patch("app.api.hs_codes.HSCodeService")
    async def test_returns_lightweight_fields(self, mock_service_class):
        """Test response contains only id, code, description_vn, description_en."""
        from app.api.hs_codes import autocomplete_hs_codes

        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.autocomplete.return_value = [
            self._make_mock_hs_code(
                id=42,
                code="85094010",
                description_vn="Máy xay sinh tố",
                description_en="Food blender",
            )
        ]

        mock_db = AsyncMock()
        result = await autocomplete_hs_codes(q="blender", limit=10, db=mock_db)

        item = result["data"][0]
        assert item["id"] == 42
        assert item["code"] == "85094010"
        assert item["description_vn"] == "Máy xay sinh tố"
        assert item["description_en"] == "Food blender"

    @pytest.mark.asyncio
    @patch("app.api.hs_codes.HSCodeService")
    async def test_no_results(self, mock_service_class):
        """Test autocomplete returns empty list when no matches."""
        from app.api.hs_codes import autocomplete_hs_codes

        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.autocomplete.return_value = []

        mock_db = AsyncMock()
        result = await autocomplete_hs_codes(q="xyznonexistent", limit=10, db=mock_db)

        assert result["success"] is True
        assert result["data"] == []

    @pytest.mark.asyncio
    @patch("app.api.hs_codes.HSCodeService")
    async def test_respects_limit(self, mock_service_class):
        """Test autocomplete passes limit parameter to service."""
        from app.api.hs_codes import autocomplete_hs_codes

        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.autocomplete.return_value = []

        mock_db = AsyncMock()
        await autocomplete_hs_codes(q="copper", limit=5, db=mock_db)

        mock_service.autocomplete.assert_awaited_once_with("copper", limit=5)

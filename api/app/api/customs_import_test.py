"""Tests for customs import API endpoints."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


def _make_test_xlsx_bytes() -> bytes:
    """Create a minimal valid XLSX file in memory and return bytes."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    # Header at row 1
    ws.append(["Mã HS", "Tên hàng"])
    ws.append(["39269099", "Vo hop nhua PC"])
    ws.append(["85414000", "Pin mat troi"])

    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    wb.save(tmp.name)
    wb.close()
    tmp.close()
    data = Path(tmp.name).read_bytes()
    Path(tmp.name).unlink(missing_ok=True)
    return data


def _make_empty_xlsx_bytes() -> bytes:
    """Create a valid XLSX with headers but no data rows."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["Mã HS", "Tên hàng"])

    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    wb.save(tmp.name)
    wb.close()
    tmp.close()
    data = Path(tmp.name).read_bytes()
    Path(tmp.name).unlink(missing_ok=True)
    return data


# Mock admin user for auth dependency
MOCK_ADMIN = {"id": 1, "email": "admin@test.com", "role": "admin"}


@pytest.fixture
def mock_admin_auth():
    """Override require_admin dependency to return mock admin."""
    from app.core.auth import require_admin

    async def _mock_require_admin():
        return MOCK_ADMIN

    app.dependency_overrides[require_admin] = _mock_require_admin
    yield
    app.dependency_overrides.pop(require_admin, None)


@pytest.fixture
def mock_db_session():
    """Override get_db_session dependency to return a mock async session."""
    from app.api.deps import get_db_session

    session = AsyncMock()
    session.add_all = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    async def _mock_get_db():
        yield session

    app.dependency_overrides[get_db_session] = _mock_get_db
    yield session
    app.dependency_overrides.pop(get_db_session, None)


class TestUploadEndpoint:
    """Tests for POST /api/admin/customs-import/upload."""

    @pytest.mark.asyncio
    async def test_upload_invalid_extension(
        self, mock_admin_auth, mock_db_session
    ):
        """Test that non-XLS/XLSX files are rejected."""
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/admin/customs-import/upload",
                files={
                    "file": ("test.csv", b"some,csv,data", "text/csv")
                },
            )

        data = response.json()
        assert data["success"] is False
        assert data["error"]["status"] == 400
        assert "XLS" in data["error"]["detail"] or "XLSX" in data["error"]["detail"]

    @pytest.mark.asyncio
    async def test_upload_valid_xlsx(
        self, mock_admin_auth, mock_db_session
    ):
        """Test successful upload and preview of a valid XLSX file."""
        xlsx_bytes = _make_test_xlsx_bytes()

        mock_preview = {
            "total_rows": 2,
            "sample_rows": [
                {
                    "product_name": "Vo hop nhua PC",
                    "hs_code": "39269099",
                    "row_number": 2,
                },
                {
                    "product_name": "Pin mat troi",
                    "hs_code": "85414000",
                    "row_number": 3,
                },
            ],
            "duplicate_count": 0,
            "unmatched_count": 0,
            "ready_to_import_count": 2,
        }

        with patch(
            "app.api.customs_import.CustomsImportService"
        ) as mock_svc:
            mock_svc.return_value.preview_import = AsyncMock(
                return_value=mock_preview
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/admin/customs-import/upload",
                    files={
                        "file": (
                            "report.xlsx",
                            xlsx_bytes,
                            XLSX_CONTENT_TYPE,
                        )
                    },
                )

        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_rows"] == 2
        assert data["data"]["ready_to_import_count"] == 2
        assert data["data"]["file_name"] == "report.xlsx"
        assert len(data["data"]["sample_rows"]) == 2

    @pytest.mark.asyncio
    async def test_upload_empty_file(
        self, mock_admin_auth, mock_db_session
    ):
        """Test upload of a file with no parseable data rows."""
        xlsx_bytes = _make_empty_xlsx_bytes()

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/admin/customs-import/upload",
                files={
                    "file": (
                        "empty.xlsx",
                        xlsx_bytes,
                        XLSX_CONTENT_TYPE,
                    )
                },
            )

        data = response.json()
        assert data["success"] is False
        assert data["error"]["status"] == 400

    @pytest.mark.asyncio
    async def test_upload_requires_admin(self):
        """Test that upload endpoint requires admin auth (no mock)."""
        app.dependency_overrides.clear()

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/admin/customs-import/upload",
                files={
                    "file": (
                        "test.xlsx",
                        b"fake",
                        "application/octet-stream",
                    )
                },
            )

        assert response.status_code == 401


class TestExecuteEndpoint:
    """Tests for POST /api/admin/customs-import/execute."""

    @pytest.mark.asyncio
    async def test_execute_invalid_extension(
        self, mock_admin_auth, mock_db_session
    ):
        """Test that non-XLS/XLSX files are rejected for execute."""
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/admin/customs-import/execute",
                files={
                    "file": ("test.pdf", b"fake", "application/pdf")
                },
            )

        data = response.json()
        assert data["success"] is False
        assert data["error"]["status"] == 400

    @pytest.mark.asyncio
    async def test_execute_valid_xlsx(
        self, mock_admin_auth, mock_db_session
    ):
        """Test successful import execution."""
        from app.services.customs_import_service import ImportResult

        xlsx_bytes = _make_test_xlsx_bytes()

        mock_result = ImportResult(
            total_rows=2,
            records_imported=2,
            duplicates_skipped=0,
            unmatched_codes=[],
            errors=[],
        )

        with patch(
            "app.api.customs_import.CustomsImportService"
        ) as mock_svc:
            mock_svc.return_value.import_rows = AsyncMock(
                return_value=mock_result
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/admin/customs-import/execute",
                    files={
                        "file": (
                            "report.xlsx",
                            xlsx_bytes,
                            XLSX_CONTENT_TYPE,
                        )
                    },
                )

        data = response.json()
        assert data["success"] is True
        assert data["data"]["records_imported"] == 2
        assert data["data"]["duplicates_skipped"] == 0
        assert data["data"]["file_name"] == "report.xlsx"
        assert "elapsed_seconds" in data["data"]

    @pytest.mark.asyncio
    async def test_execute_empty_file(
        self, mock_admin_auth, mock_db_session
    ):
        """Test execute endpoint rejects file with headers but no data rows."""
        xlsx_bytes = _make_empty_xlsx_bytes()

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/admin/customs-import/execute",
                files={
                    "file": (
                        "empty.xlsx",
                        xlsx_bytes,
                        XLSX_CONTENT_TYPE,
                    )
                },
            )

        data = response.json()
        assert data["success"] is False
        assert data["error"]["status"] == 400

    @pytest.mark.asyncio
    async def test_execute_requires_admin(self):
        """Test that execute endpoint requires admin auth."""
        app.dependency_overrides.clear()

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/admin/customs-import/execute",
                files={
                    "file": (
                        "test.xlsx",
                        b"fake",
                        "application/octet-stream",
                    )
                },
            )

        assert response.status_code == 401

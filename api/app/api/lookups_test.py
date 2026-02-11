"""Tests for lookups API endpoint."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_mock_record(
    id: int = 1,
    query_text: str = "copper towel rack",
    query_language: str | None = "en",
    confidence_score: float | None = 85.0,
    search_method: str = "vector",
    is_verified: bool = False,
    hs_code: str | None = "74182000",
    description_vn: str | None = "Thanh treo khan dong",
) -> MagicMock:
    """Create a mock LookupRecord with matched HS code."""
    record = MagicMock()
    record.id = id
    record.query_text = query_text
    record.query_language = query_language
    record.confidence_score = confidence_score
    record.search_method = search_method
    record.is_verified = is_verified
    record.created_at = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)

    if hs_code:
        record.matched_hs_code = MagicMock()
        record.matched_hs_code.code = hs_code
        record.matched_hs_code.description_vn = description_vn
    else:
        record.matched_hs_code = None

    return record


class TestListLookups:
    """Tests for GET /api/lookups endpoint."""

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_list_lookups_success(self, mock_get_db, mock_repo_class):
        """Test successful paginated list retrieval."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        records = [_make_mock_record(id=1), _make_mock_record(id=2)]
        mock_repo = AsyncMock()
        mock_repo.get_all_with_hs_codes.return_value = records
        mock_repo.count_all.return_value = 2
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups?limit=20&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 2
        assert data["data"]["total"] == 2
        assert data["data"]["limit"] == 20
        assert data["data"]["offset"] == 0

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_list_lookups_item_fields(self, mock_get_db, mock_repo_class):
        """Test that each item has all required fields."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        records = [_make_mock_record()]
        mock_repo = AsyncMock()
        mock_repo.get_all_with_hs_codes.return_value = records
        mock_repo.count_all.return_value = 1
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups")

        assert response.status_code == 200
        item = response.json()["data"]["items"][0]
        assert item["id"] == 1
        assert item["query_text"] == "copper towel rack"
        assert item["query_language"] == "en"
        assert item["matched_hs_code"] == "74182000"
        assert item["matched_description_vn"] == "Thanh treo khan dong"
        assert item["confidence_score"] == 85.0
        assert item["search_method"] == "vector"
        assert item["is_verified"] is False
        assert "created_at" in item

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_list_lookups_no_matched_hs_code(self, mock_get_db, mock_repo_class):
        """Test item with no matched HS code returns null fields."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        records = [_make_mock_record(hs_code=None)]
        mock_repo = AsyncMock()
        mock_repo.get_all_with_hs_codes.return_value = records
        mock_repo.count_all.return_value = 1
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups")

        assert response.status_code == 200
        item = response.json()["data"]["items"][0]
        assert item["matched_hs_code"] is None
        assert item["matched_description_vn"] is None

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_list_lookups_verified_filter_true(self, mock_get_db, mock_repo_class):
        """Test filtering by verified=true."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        mock_repo = AsyncMock()
        mock_repo.get_all_with_hs_codes.return_value = []
        mock_repo.count_all.return_value = 0
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups?verified=true")

        assert response.status_code == 200
        mock_repo.get_all_with_hs_codes.assert_awaited_once_with(
            limit=20, offset=0, verified_filter=True
        )
        mock_repo.count_all.assert_awaited_once_with(verified_filter=True)

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_list_lookups_verified_filter_false(self, mock_get_db, mock_repo_class):
        """Test filtering by verified=false."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        mock_repo = AsyncMock()
        mock_repo.get_all_with_hs_codes.return_value = []
        mock_repo.count_all.return_value = 0
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups?verified=false")

        assert response.status_code == 200
        mock_repo.get_all_with_hs_codes.assert_awaited_once_with(
            limit=20, offset=0, verified_filter=False
        )

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_list_lookups_no_filter(self, mock_get_db, mock_repo_class):
        """Test no verified filter returns all records."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        mock_repo = AsyncMock()
        mock_repo.get_all_with_hs_codes.return_value = []
        mock_repo.count_all.return_value = 0
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups")

        assert response.status_code == 200
        mock_repo.get_all_with_hs_codes.assert_awaited_once_with(
            limit=20, offset=0, verified_filter=None
        )

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_list_lookups_empty(self, mock_get_db, mock_repo_class):
        """Test empty result returns correct structure."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        mock_repo = AsyncMock()
        mock_repo.get_all_with_hs_codes.return_value = []
        mock_repo.count_all.return_value = 0
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    def test_list_lookups_invalid_limit_negative(self):
        """Test that negative limit returns 400 error."""
        response = client.get("/api/lookups?limit=-1")

        assert response.status_code == 200  # envelope always 200
        data = response.json()
        assert data["success"] is False
        assert data["error"]["status"] == 400
        assert "limit" in data["error"]["detail"]

    def test_list_lookups_invalid_limit_zero(self):
        """Test that limit=0 returns 400 error."""
        response = client.get("/api/lookups?limit=0")

        data = response.json()
        assert data["success"] is False
        assert data["error"]["status"] == 400

    def test_list_lookups_invalid_limit_too_large(self):
        """Test that limit > 100 returns 400 error."""
        response = client.get("/api/lookups?limit=101")

        data = response.json()
        assert data["success"] is False
        assert data["error"]["status"] == 400

    def test_list_lookups_invalid_offset_negative(self):
        """Test that negative offset returns 400 error."""
        response = client.get("/api/lookups?offset=-1")

        data = response.json()
        assert data["success"] is False
        assert data["error"]["status"] == 400
        assert "offset" in data["error"]["detail"]

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_list_lookups_envelope_format(self, mock_get_db, mock_repo_class):
        """Test response follows envelope format."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        mock_repo = AsyncMock()
        mock_repo.get_all_with_hs_codes.return_value = []
        mock_repo.count_all.return_value = 0
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups")

        data = response.json()
        assert "success" in data
        assert "data" in data
        assert "error" in data

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_list_lookups_custom_pagination(self, mock_get_db, mock_repo_class):
        """Test custom limit and offset are passed to repository."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        mock_repo = AsyncMock()
        mock_repo.get_all_with_hs_codes.return_value = []
        mock_repo.count_all.return_value = 0
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups?limit=5&offset=10")

        assert response.status_code == 200
        mock_repo.get_all_with_hs_codes.assert_awaited_once_with(
            limit=5, offset=10, verified_filter=None
        )

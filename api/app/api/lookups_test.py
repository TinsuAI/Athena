"""Tests for lookups API endpoint."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_mock_detail_record(
    id: int = 1,
    query_text: str = "copper towel rack",
    query_language: str | None = "en",
    confidence_score: float | None = 85.0,
    search_method: str = "vector",
    is_verified: bool = False,
    verified_at: datetime | None = None,
    notes: str | None = None,
    classification_data: dict | None = None,
    practical_notes: list | None = None,
    process_logs: list | None = None,
    nlm_raw_response: str | None = None,
    matched_hs_code: MagicMock | None = "default",
    correct_hs_code: MagicMock | None = None,
) -> MagicMock:
    """Create a mock LookupRecord with full detail fields."""
    record = MagicMock()
    record.id = id
    record.query_text = query_text
    record.query_language = query_language
    record.confidence_score = confidence_score
    record.search_method = search_method
    record.is_verified = is_verified
    record.verified_at = verified_at
    record.notes = notes
    record.classification_data = classification_data
    record.practical_notes = practical_notes
    record.process_logs = process_logs
    record.nlm_raw_response = nlm_raw_response
    record.created_at = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)

    if matched_hs_code == "default":
        hs = MagicMock()
        hs.code = "7418.20.00"
        hs.description_vn = "Thanh treo khăn đồng"
        hs.description_en = "Copper towel rack"
        hs.duty_rate = "30%"
        hs.vat_rate = "10%"
        record.matched_hs_code = hs
    else:
        record.matched_hs_code = matched_hs_code

    record.correct_hs_code = correct_hs_code
    return record


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


class TestGetLookupDetail:
    """Tests for GET /api/lookups/{id} endpoint."""

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_get_detail_success(self, mock_get_db, mock_repo_class):
        """Test successful detail retrieval with all fields."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        record = _make_mock_detail_record(
            classification_data={
                "material": "Copper alloy",
                "function": "Bathroom fixture",
            },
            practical_notes=["Import note 1", "Import note 2"],
            process_logs=[{
                "step": "init",
                "status": "completed",
                "message": "Started",
                "duration_ms": 5,
            }],
        )
        mock_repo = AsyncMock()
        mock_repo.find_by_id_with_details.return_value = record
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups/1")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        detail = data["data"]
        assert detail["id"] == 1
        assert detail["query_text"] == "copper towel rack"
        assert detail["query_language"] == "en"
        assert detail["matched_hs_code"]["code"] == "7418.20.00"
        assert detail["matched_hs_code"]["description_vn"] == "Thanh treo khăn đồng"
        assert detail["matched_hs_code"]["duty_rate"] == "30%"
        assert detail["matched_hs_code"]["vat_rate"] == "10%"
        assert detail["correct_hs_code"] is None
        assert detail["classification_data"]["material"] == "Copper alloy"
        assert detail["practical_notes"] == ["Import note 1", "Import note 2"]
        assert len(detail["process_logs"]) == 1
        assert detail["confidence_score"] == 85.0
        assert detail["search_method"] == "vector"
        assert detail["is_verified"] is False
        assert detail["verified_at"] is None
        assert detail["notes"] is None
        assert "created_at" in detail

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_get_detail_not_found(self, mock_get_db, mock_repo_class):
        """Test 404 error for non-existent lookup record."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        mock_repo = AsyncMock()
        mock_repo.find_by_id_with_details.return_value = None
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups/99999")

        assert response.status_code == 200  # envelope always 200
        data = response.json()
        assert data["success"] is False
        assert data["error"]["status"] == 404
        assert "99999" in data["error"]["detail"]

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_get_detail_verified_with_correction(self, mock_get_db, mock_repo_class):
        """Test detail of a verified record with correct HS code."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        correct_hs = MagicMock()
        correct_hs.code = "7418.10.00"
        correct_hs.description_vn = "Bồn rửa đồng"
        correct_hs.description_en = "Copper sink"
        correct_hs.duty_rate = "25%"
        correct_hs.vat_rate = "10%"

        record = _make_mock_detail_record(
            is_verified=True,
            verified_at=datetime(2026, 2, 11, 10, 0, 0, tzinfo=timezone.utc),
            notes="Corrected by expert",
            correct_hs_code=correct_hs,
        )
        mock_repo = AsyncMock()
        mock_repo.find_by_id_with_details.return_value = record
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups/1")

        assert response.status_code == 200
        detail = response.json()["data"]
        assert detail["is_verified"] is True
        assert detail["verified_at"] is not None
        assert detail["notes"] == "Corrected by expert"
        assert detail["correct_hs_code"]["code"] == "7418.10.00"
        assert detail["correct_hs_code"]["description_vn"] == "Bồn rửa đồng"
        assert detail["correct_hs_code"]["duty_rate"] == "25%"

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_get_detail_no_matched_hs_code(self, mock_get_db, mock_repo_class):
        """Test detail when matched HS code is null."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        record = _make_mock_detail_record(matched_hs_code=None)
        mock_repo = AsyncMock()
        mock_repo.find_by_id_with_details.return_value = record
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups/1")

        assert response.status_code == 200
        detail = response.json()["data"]
        assert detail["matched_hs_code"] is None

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_get_detail_null_jsonb_fields(self, mock_get_db, mock_repo_class):
        """Test detail when JSONB fields are null."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        record = _make_mock_detail_record(
            classification_data=None,
            practical_notes=None,
            process_logs=None,
        )
        mock_repo = AsyncMock()
        mock_repo.find_by_id_with_details.return_value = record
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups/1")

        assert response.status_code == 200
        detail = response.json()["data"]
        assert detail["classification_data"] is None
        assert detail["practical_notes"] is None
        assert detail["process_logs"] is None

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_get_detail_envelope_format(self, mock_get_db, mock_repo_class):
        """Test response follows envelope format."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        record = _make_mock_detail_record()
        mock_repo = AsyncMock()
        mock_repo.find_by_id_with_details.return_value = record
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups/1")

        data = response.json()
        assert "success" in data
        assert "data" in data
        assert "error" in data

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_get_detail_includes_nlm_raw_response(self, mock_get_db, mock_repo_class):
        """AC6: GET /api/lookups/{id} includes nlm_raw_response when present."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        raw_response = "## HS Code: 7418.20.00\n\nCopper towel rack classification..."
        record = _make_mock_detail_record(
            search_method="notebooklm",
            nlm_raw_response=raw_response,
        )
        mock_repo = AsyncMock()
        mock_repo.find_by_id_with_details.return_value = record
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups/1")

        assert response.status_code == 200
        detail = response.json()["data"]
        assert detail["nlm_raw_response"] == raw_response

    @patch("app.api.lookups.LookupRecordRepository")
    @patch("app.api.lookups.get_db")
    def test_get_detail_nlm_raw_response_null_for_non_nlm(self, mock_get_db, mock_repo_class):
        """AC8: Non-NLM lookups have nlm_raw_response as null."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        record = _make_mock_detail_record(
            search_method="vector",
            nlm_raw_response=None,
        )
        mock_repo = AsyncMock()
        mock_repo.find_by_id_with_details.return_value = record
        mock_repo_class.return_value = mock_repo

        response = client.get("/api/lookups/1")

        assert response.status_code == 200
        detail = response.json()["data"]
        assert detail["nlm_raw_response"] is None

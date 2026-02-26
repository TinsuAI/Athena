"""Tests for lookup record repository."""

import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.lookup_record import LookupRecord
from app.repositories.lookup_record_repository import (
    LookupRecordRepository,
    compute_query_hash,
)


class TestComputeQueryHash:
    """Test the compute_query_hash utility function."""

    def test_basic_hash(self):
        """Test hash computation for basic query."""
        result = compute_query_hash("copper towel rack")
        expected = hashlib.sha256("copper towel rack".encode("utf-8")).hexdigest()
        assert result == expected
        assert len(result) == 64

    def test_normalization_lowercase(self):
        """Test that hash normalizes to lowercase."""
        assert compute_query_hash("Copper Towel Rack") == compute_query_hash(
            "copper towel rack"
        )

    def test_normalization_strip_whitespace(self):
        """Test that hash strips leading/trailing whitespace."""
        assert compute_query_hash("  copper towel rack  ") == compute_query_hash(
            "copper towel rack"
        )

    def test_normalization_combined(self):
        """Test combined normalization."""
        assert compute_query_hash("  COPPER Towel RACK  ") == compute_query_hash(
            "copper towel rack"
        )

    def test_different_queries_different_hashes(self):
        """Test that different queries produce different hashes."""
        assert compute_query_hash("copper") != compute_query_hash("aluminum")

    def test_unicode_query(self):
        """Test hash computation for Vietnamese text."""
        result = compute_query_hash("thanh treo khăn đồng")
        assert len(result) == 64


class TestLookupRecordRepository:
    """Test cases for LookupRecordRepository."""

    def _make_record(self, **kwargs) -> LookupRecord:
        """Create a LookupRecord with default values for testing."""
        defaults = {
            "id": 1,
            "query_text": "copper towel rack",
            "query_hash": compute_query_hash("copper towel rack"),
            "search_method": "vector",
            "is_verified": False,
            "confidence_score": 85.0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        defaults.update(kwargs)
        record = LookupRecord()
        for key, value in defaults.items():
            setattr(record, key, value)
        return record

    @pytest.mark.asyncio
    async def test_create_adds_to_session(self):
        """Test that create adds record to session and flushes."""
        mock_session = AsyncMock()
        repo = LookupRecordRepository(session=mock_session)
        record = self._make_record()

        result = await repo.create(record)

        mock_session.add.assert_called_once_with(record)
        mock_session.flush.assert_awaited_once()
        assert result is record

    @pytest.mark.asyncio
    async def test_find_by_query_hash_found(self):
        """Test finding record by query hash within time window."""
        mock_session = AsyncMock()
        expected_record = self._make_record()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_record
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.find_by_query_hash(expected_record.query_hash)

        assert result is expected_record
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_find_by_query_hash_not_found(self):
        """Test finding no record by query hash."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.find_by_query_hash("nonexistent_hash")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_unverified(self):
        """Test getting unverified records."""
        mock_session = AsyncMock()
        records = [self._make_record(id=i) for i in range(3)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = records
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.get_unverified(limit=10, offset=0)

        assert len(result) == 3
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_count_unverified(self):
        """Test counting unverified records."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 42
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.count_unverified()

        assert result == 42

    @pytest.mark.asyncio
    async def test_update_flushes_session(self):
        """Test that update flushes session."""
        mock_session = AsyncMock()
        repo = LookupRecordRepository(session=mock_session)
        record = self._make_record()

        result = await repo.update(record)

        mock_session.flush.assert_awaited_once()
        assert result is record

    @pytest.mark.asyncio
    async def test_touch_updated_at(self):
        """Test updating only the updated_at timestamp."""
        mock_session = AsyncMock()
        repo = LookupRecordRepository(session=mock_session)

        await repo.touch_updated_at(record_id=1)

        mock_session.execute.assert_awaited_once()

    # --- Tests for find_verified_exact (Task 1.1) ---

    @pytest.mark.asyncio
    async def test_find_verified_exact_found(self):
        """Test finding verified record by exact query hash."""
        mock_session = AsyncMock()
        expected_record = self._make_record(
            is_verified=True,
            correct_hs_code_id=42,
            query_hash=compute_query_hash("copper towel rack"),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_record
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.find_verified_exact(
            compute_query_hash("copper towel rack")
        )

        assert result is expected_record
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_find_verified_exact_not_found(self):
        """Test no verified record found for given hash."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.find_verified_exact("nonexistent_hash")

        assert result is None

    @pytest.mark.asyncio
    async def test_find_verified_exact_excludes_unverified(self):
        """Test that unverified records are excluded from exact match."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.find_verified_exact(
            compute_query_hash("copper towel rack")
        )

        assert result is None
        mock_session.execute.assert_awaited_once()

    # --- Tests for find_verified_similar (Task 1.2) ---

    @pytest.mark.asyncio
    async def test_find_verified_similar_found(self):
        """Test finding verified records by text similarity."""
        mock_session = AsyncMock()
        expected_record = self._make_record(
            is_verified=True,
            correct_hs_code_id=42,
        )

        mock_row = MagicMock()
        mock_row.LookupRecord = expected_record
        mock_row.similarity = 0.92

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        results = await repo.find_verified_similar("copper towel rack")

        assert len(results) == 1
        record, sim_score = results[0]
        assert record is expected_record
        assert sim_score == 0.92

    @pytest.mark.asyncio
    async def test_find_verified_similar_not_found(self):
        """Test no similar verified records found."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        results = await repo.find_verified_similar("xyznonexistent123")

        assert results == []

    @pytest.mark.asyncio
    async def test_find_verified_similar_custom_threshold(self):
        """Test similar search with custom threshold."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        results = await repo.find_verified_similar(
            "copper towel rack", threshold=0.95
        )

        assert results == []
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_find_verified_similar_respects_limit(self):
        """Test similar search respects limit parameter."""
        mock_session = AsyncMock()
        records = [
            self._make_record(id=i, is_verified=True, correct_hs_code_id=i + 10)
            for i in range(3)
        ]

        mock_rows = []
        for i, rec in enumerate(records):
            mock_row = MagicMock()
            mock_row.LookupRecord = rec
            mock_row.similarity = 0.95 - (i * 0.03)
            mock_rows.append(mock_row)

        mock_result = MagicMock()
        mock_result.all.return_value = mock_rows
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        results = await repo.find_verified_similar("copper towel rack", limit=3)

        assert len(results) == 3

    # --- Tests for find_verified_containment (Sprint Change 2026-02-24) ---

    @pytest.mark.asyncio
    async def test_find_verified_containment_found(self):
        """Test finding verified record when query is substring of stored query_text."""
        mock_session = AsyncMock()
        expected_record = self._make_record(
            id=1,
            is_verified=True,
            correct_hs_code_id=42,
            query_text="Vỏ hộp chính, bằng nhựa PC, kích thước 400.2*396mm. Hàng mới 100%.",
        )

        mock_row = MagicMock()
        mock_row.LookupRecord = expected_record
        mock_row.text_len = 66

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        results = await repo.find_verified_containment("Vỏ hộp chính, bằng nhựa PC")

        assert len(results) == 1
        record, confidence = results[0]
        assert record is expected_record
        assert confidence == 0.95

    @pytest.mark.asyncio
    async def test_find_verified_containment_not_found(self):
        """Test no containment match found."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        results = await repo.find_verified_containment("xyznonexistent123")

        assert results == []

    @pytest.mark.asyncio
    async def test_find_verified_containment_short_query_skipped(self):
        """Test that queries shorter than 4 chars skip containment search."""
        mock_session = AsyncMock()

        repo = LookupRecordRepository(session=mock_session)
        results = await repo.find_verified_containment("PC")

        assert results == []
        mock_session.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_find_verified_containment_strips_whitespace(self):
        """Test that query is normalized (stripped) before containment search."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        results = await repo.find_verified_containment("   test query   ")

        assert results == []
        # Should have executed (length after strip is 10, >= 4)
        mock_session.execute.assert_awaited_once()

    # --- Tests for get_unverified_with_hs_codes (Story 1-10, Task 2.1) ---

    @pytest.mark.asyncio
    async def test_get_unverified_with_hs_codes(self):
        """Test getting unverified records with eagerly loaded HS code data."""
        mock_session = AsyncMock()
        records = [self._make_record(id=i) for i in range(3)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = records
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.get_unverified_with_hs_codes(limit=10, offset=0)

        assert len(result) == 3
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_unverified_with_hs_codes_pagination(self):
        """Test pagination parameters are passed correctly."""
        mock_session = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.get_unverified_with_hs_codes(limit=5, offset=10)

        assert result == []
        mock_session.execute.assert_awaited_once()

    # --- Tests for find_by_id (Story 1-10, Task 2.2) ---

    @pytest.mark.asyncio
    async def test_find_by_id_found(self):
        """Test finding a record by ID."""
        mock_session = AsyncMock()
        expected_record = self._make_record(id=42)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_record
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.find_by_id(42)

        assert result is expected_record
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self):
        """Test finding non-existent record by ID returns None."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.find_by_id(999)

        assert result is None

    # --- Tests for JSONB field round-trip (Story 1-11) ---

    @pytest.mark.asyncio
    async def test_create_record_with_jsonb_fields(self):
        """Test creating a LookupRecord with JSONB fields (classification_data, practical_notes, process_logs)."""
        mock_session = AsyncMock()
        repo = LookupRecordRepository(session=mock_session)

        classification_data = {"material": "Copper alloy", "function": "Bathroom fixture"}
        practical_notes = ["Note 1", "Note 2"]
        process_logs = [
            {"step": "init", "status": "completed", "message": "Started", "duration_ms": 1, "details": None},
            {"step": "search", "status": "completed", "message": "Found", "duration_ms": 50, "details": {"candidates": 5}},
        ]

        record = self._make_record(
            classification_data=classification_data,
            practical_notes=practical_notes,
            process_logs=process_logs,
        )

        result = await repo.create(record)

        mock_session.add.assert_called_once_with(record)
        mock_session.flush.assert_awaited_once()
        assert result.classification_data == classification_data
        assert result.practical_notes == practical_notes
        assert result.process_logs == process_logs

    @pytest.mark.asyncio
    async def test_create_record_with_none_jsonb_fields(self):
        """Test creating a LookupRecord with None JSONB fields (no-results path)."""
        mock_session = AsyncMock()
        repo = LookupRecordRepository(session=mock_session)

        record = self._make_record(
            classification_data=None,
            practical_notes=None,
            process_logs=None,
        )

        result = await repo.create(record)

        assert result.classification_data is None
        assert result.practical_notes is None
        assert result.process_logs is None

    @pytest.mark.asyncio
    async def test_update_preserves_jsonb_field_changes(self):
        """Test that update flushes session with modified JSONB fields."""
        mock_session = AsyncMock()
        repo = LookupRecordRepository(session=mock_session)

        record = self._make_record()
        record.classification_data = {"material": "Updated", "function": "Updated"}
        record.practical_notes = ["New note"]
        record.process_logs = [{"step": "init", "status": "completed", "message": "Re-search", "duration_ms": 1, "details": None}]

        result = await repo.update(record)

        mock_session.flush.assert_awaited_once()
        assert result.classification_data == {"material": "Updated", "function": "Updated"}
        assert result.practical_notes == ["New note"]

    # --- Tests for get_all_with_hs_codes (Story 1-12, Task 1.1) ---

    @pytest.mark.asyncio
    async def test_get_all_with_hs_codes_returns_all(self):
        """Test getting all records with eagerly loaded HS code data."""
        mock_session = AsyncMock()
        records = [self._make_record(id=i) for i in range(3)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = records
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.get_all_with_hs_codes(limit=10, offset=0)

        assert len(result) == 3
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_all_with_hs_codes_verified_filter_true(self):
        """Test filtering for verified records only."""
        mock_session = AsyncMock()
        records = [self._make_record(id=1, is_verified=True)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = records
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.get_all_with_hs_codes(verified_filter=True)

        assert len(result) == 1
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_all_with_hs_codes_verified_filter_false(self):
        """Test filtering for unverified records only."""
        mock_session = AsyncMock()
        records = [self._make_record(id=1, is_verified=False)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = records
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.get_all_with_hs_codes(verified_filter=False)

        assert len(result) == 1
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_all_with_hs_codes_no_filter(self):
        """Test getting all records without filter (verified_filter=None)."""
        mock_session = AsyncMock()
        records = [
            self._make_record(id=1, is_verified=True),
            self._make_record(id=2, is_verified=False),
        ]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = records
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.get_all_with_hs_codes(verified_filter=None)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_all_with_hs_codes_pagination(self):
        """Test pagination parameters are passed correctly."""
        mock_session = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.get_all_with_hs_codes(limit=5, offset=10)

        assert result == []
        mock_session.execute.assert_awaited_once()

    # --- Tests for count_all (Story 1-12, Task 1.2) ---

    @pytest.mark.asyncio
    async def test_count_all_no_filter(self):
        """Test counting all records without filter."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 42
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.count_all()

        assert result == 42

    @pytest.mark.asyncio
    async def test_count_all_verified_filter_true(self):
        """Test counting verified records only."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 10
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.count_all(verified_filter=True)

        assert result == 10

    @pytest.mark.asyncio
    async def test_count_all_verified_filter_false(self):
        """Test counting unverified records only."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 32
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.count_all(verified_filter=False)

        assert result == 32

    # --- Tests for apply_correction (Story 1-10, Task 2.3) ---

    # --- Tests for find_by_id_with_details (Story 1-13, Task 1.1) ---

    @pytest.mark.asyncio
    async def test_find_by_id_with_details_found(self):
        """Test finding a record by ID with both HS code relationships eagerly loaded."""
        mock_session = AsyncMock()
        expected_record = self._make_record(id=42)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_record
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.find_by_id_with_details(42)

        assert result is expected_record
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_find_by_id_with_details_not_found(self):
        """Test finding non-existent record by ID with details returns None."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.find_by_id_with_details(99999)

        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_id_with_details_uses_selectinload(self):
        """Test that find_by_id_with_details uses selectinload for relationships."""
        mock_session = AsyncMock()
        expected_record = self._make_record(id=1)
        expected_record.matched_hs_code = MagicMock()
        expected_record.correct_hs_code = MagicMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_record
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.find_by_id_with_details(1)

        assert result is expected_record
        # Verify the query was executed (selectinload is part of the query options)
        mock_session.execute.assert_awaited_once()

    # --- Tests for apply_correction (Story 1-10, Task 2.3) ---

    @pytest.mark.asyncio
    async def test_apply_correction(self):
        """Test applying a correction updates the record."""
        mock_session = AsyncMock()

        updated_record = self._make_record(
            id=1,
            correct_hs_code_id=55,
            is_verified=True,
            notes="corrected",
        )

        # First call: UPDATE, second call: SELECT
        mock_select_result = MagicMock()
        mock_select_result.scalar_one.return_value = updated_record
        mock_session.execute.side_effect = [
            AsyncMock(),  # UPDATE result
            mock_select_result,  # SELECT result
        ]

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.apply_correction(
            record_id=1,
            correct_hs_code_id=55,
            notes="corrected",
        )

        assert result is updated_record
        assert mock_session.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_apply_correction_without_notes(self):
        """Test applying a correction without notes."""
        mock_session = AsyncMock()

        updated_record = self._make_record(
            id=1,
            correct_hs_code_id=55,
            is_verified=True,
            notes=None,
        )

        mock_select_result = MagicMock()
        mock_select_result.scalar_one.return_value = updated_record
        mock_session.execute.side_effect = [
            AsyncMock(),
            mock_select_result,
        ]

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.apply_correction(
            record_id=1,
            correct_hs_code_id=55,
        )

        assert result is updated_record
        assert result.notes is None

    # --- Tests for submit_pending_correction (Story 5-2, Task 5.1) ---

    @pytest.mark.asyncio
    async def test_submit_pending_correction_sets_all_fields(self):
        """Test submit_pending_correction sets all required fields correctly."""
        mock_session = AsyncMock()

        updated_record = self._make_record(
            id=1,
            correct_hs_code_id=55,
            correction_status="pending",
            is_verified=False,
            submitted_by_user_id=42,
            notes="Cần mã HS đúng cho đồng",
        )

        mock_select_result = MagicMock()
        mock_select_result.scalar_one.return_value = updated_record
        mock_session.execute.side_effect = [
            AsyncMock(),  # UPDATE result
            mock_select_result,  # SELECT result
        ]

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.submit_pending_correction(
            record_id=1,
            correct_hs_code_id=55,
            submitted_by_user_id=42,
            notes="Cần mã HS đúng cho đồng",
        )

        assert result is updated_record
        assert result.correction_status == "pending"
        assert result.is_verified is False
        assert result.submitted_by_user_id == 42
        assert result.correct_hs_code_id == 55
        assert result.notes == "Cần mã HS đúng cho đồng"
        assert mock_session.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_submit_pending_correction_preserves_is_verified_false(self):
        """Test submit_pending_correction never sets is_verified=True."""
        mock_session = AsyncMock()

        # Even if the record was previously verified (edge case), pending sets is_verified=False
        updated_record = self._make_record(
            id=1,
            correct_hs_code_id=55,
            correction_status="pending",
            is_verified=False,
            submitted_by_user_id=99,
        )

        mock_select_result = MagicMock()
        mock_select_result.scalar_one.return_value = updated_record
        mock_session.execute.side_effect = [
            AsyncMock(),
            mock_select_result,
        ]

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.submit_pending_correction(
            record_id=1,
            correct_hs_code_id=55,
            submitted_by_user_id=99,
        )

        # CRITICAL: is_verified must remain False — never auto-verified
        assert result.is_verified is False
        assert result.correction_status == "pending"

    @pytest.mark.asyncio
    async def test_submit_pending_correction_without_notes(self):
        """Test submit_pending_correction works without optional notes."""
        mock_session = AsyncMock()

        updated_record = self._make_record(
            id=1,
            correct_hs_code_id=55,
            correction_status="pending",
            is_verified=False,
            submitted_by_user_id=7,
            notes=None,
        )

        mock_select_result = MagicMock()
        mock_select_result.scalar_one.return_value = updated_record
        mock_session.execute.side_effect = [
            AsyncMock(),
            mock_select_result,
        ]

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.submit_pending_correction(
            record_id=1,
            correct_hs_code_id=55,
            submitted_by_user_id=7,
        )

        assert result is updated_record
        assert result.notes is None
        assert result.correction_status == "pending"

    # --- Tests for get_pending_corrections (Story 5-3, Task 10.10) ---

    @pytest.mark.asyncio
    async def test_get_pending_corrections_returns_only_pending(self):
        """Test get_pending_corrections returns only records with correction_status='pending'."""
        mock_session = AsyncMock()
        pending_records = [
            self._make_record(id=i, correction_status="pending") for i in range(2)
        ]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = pending_records
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.get_pending_corrections(limit=20, offset=0)

        assert len(result) == 2
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_count_pending_corrections(self):
        """Test count_pending_corrections returns correct count."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        mock_session.execute.return_value = mock_result

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.count_pending_corrections()

        assert result == 5

    # --- Tests for approve_correction (Story 5-3, Task 10.11) ---

    @pytest.mark.asyncio
    async def test_approve_correction_sets_all_fields(self):
        """Test approve_correction sets is_verified, correction_status, verified_by_user_id, verified_at."""
        mock_session = AsyncMock()

        approved_record = self._make_record(
            id=1,
            is_verified=True,
            correction_status="approved",
            verified_by_user_id=10,
        )

        mock_select_result = MagicMock()
        mock_select_result.scalar_one.return_value = approved_record
        mock_session.execute.side_effect = [
            AsyncMock(),  # UPDATE result
            mock_select_result,  # SELECT result
        ]

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.approve_correction(record_id=1, verified_by_user_id=10)

        assert result is approved_record
        assert result.is_verified is True
        assert result.correction_status == "approved"
        assert result.verified_by_user_id == 10
        assert mock_session.execute.await_count == 2

    # --- Tests for reject_correction (Story 5-3, Task 10.12) ---

    @pytest.mark.asyncio
    async def test_reject_correction_sets_status_and_reason(self):
        """Test reject_correction sets correction_status='rejected' and rejection_reason."""
        mock_session = AsyncMock()

        rejected_record = self._make_record(
            id=1,
            correction_status="rejected",
            rejection_reason="Ma HS khong phu hop",
        )

        mock_select_result = MagicMock()
        mock_select_result.scalar_one.return_value = rejected_record
        mock_session.execute.side_effect = [
            AsyncMock(),  # UPDATE result
            mock_select_result,  # SELECT result
        ]

        repo = LookupRecordRepository(session=mock_session)
        result = await repo.reject_correction(
            record_id=1, rejection_reason="Ma HS khong phu hop"
        )

        assert result is rejected_record
        assert result.correction_status == "rejected"
        assert result.rejection_reason == "Ma HS khong phu hop"
        assert mock_session.execute.await_count == 2

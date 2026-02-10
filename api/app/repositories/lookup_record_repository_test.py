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

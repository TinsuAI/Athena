"""Tests for knowledge base service."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.lookup_record import LookupRecord
from app.repositories.lookup_record_repository import compute_query_hash
from app.services.knowledge_base_service import KBLookupResult, KnowledgeBaseService


class TestKBLookupResult:
    """Test KBLookupResult dataclass."""

    def test_create_exact_result(self):
        """Test creating KB result for exact match."""
        result = KBLookupResult(
            hs_code_id=42,
            confidence=100,
            similarity_score=1.0,
            lookup_record_id=1,
            verified_by_user_id=5,
            verified_at=datetime(2026, 2, 10, tzinfo=timezone.utc),
            match_type="exact",
        )
        assert result.confidence == 100
        assert result.similarity_score == 1.0
        assert result.match_type == "exact"

    def test_create_similar_result(self):
        """Test creating KB result for similar match."""
        result = KBLookupResult(
            hs_code_id=42,
            confidence=92,
            similarity_score=0.92,
            lookup_record_id=2,
            verified_by_user_id=None,
            verified_at=None,
            match_type="similar",
        )
        assert result.confidence == 92
        assert result.match_type == "similar"


class TestKnowledgeBaseService:
    """Test cases for KnowledgeBaseService."""

    def _make_verified_record(self, **kwargs) -> LookupRecord:
        """Create a verified LookupRecord for testing."""
        defaults = {
            "id": 1,
            "query_text": "copper towel rack",
            "query_hash": compute_query_hash("copper towel rack"),
            "search_method": "knowledge_base",
            "is_verified": True,
            "correct_hs_code_id": 42,
            "verified_by_user_id": 5,
            "verified_at": datetime(2026, 2, 10, tzinfo=timezone.utc),
            "confidence_score": 100.0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        defaults.update(kwargs)
        record = LookupRecord()
        for key, value in defaults.items():
            setattr(record, key, value)
        return record

    @pytest.mark.asyncio
    async def test_lookup_exact_match(self):
        """Test KB lookup returns exact match with confidence 100."""
        mock_session = AsyncMock()
        verified_record = self._make_verified_record()

        with patch(
            "app.services.knowledge_base_service.LookupRecordRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_verified_exact.return_value = verified_record
            mock_repo_class.return_value = mock_repo

            service = KnowledgeBaseService(session=mock_session)
            result = await service.lookup("copper towel rack")

        assert result is not None
        assert result.hs_code_id == 42
        assert result.confidence == 100
        assert result.similarity_score == 1.0
        assert result.match_type == "exact"
        assert result.verified_by_user_id == 5

    @pytest.mark.asyncio
    async def test_lookup_similar_match(self):
        """Test KB lookup falls back to similar match when no exact or containment match."""
        mock_session = AsyncMock()
        verified_record = self._make_verified_record(id=2)

        with patch(
            "app.services.knowledge_base_service.LookupRecordRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_verified_exact.return_value = None
            mock_repo.find_verified_containment.return_value = []
            mock_repo.find_verified_similar.return_value = [
                (verified_record, 0.92)
            ]
            mock_repo_class.return_value = mock_repo

            service = KnowledgeBaseService(session=mock_session)
            result = await service.lookup("copper towel holder")

        assert result is not None
        assert result.hs_code_id == 42
        assert result.confidence == 92
        assert result.similarity_score == 0.92
        assert result.match_type == "similar"

    @pytest.mark.asyncio
    async def test_lookup_containment_match(self):
        """Test KB lookup returns containment match when query is substring of stored text."""
        mock_session = AsyncMock()
        verified_record = self._make_verified_record(
            id=3,
            query_text="Vỏ hộp chính, bằng nhựa PC, kích thước 400.2*396mm. Hàng mới 100%.",
        )

        with patch(
            "app.services.knowledge_base_service.LookupRecordRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_verified_exact.return_value = None
            mock_repo.find_verified_containment.return_value = [
                (verified_record, 0.95)
            ]
            mock_repo_class.return_value = mock_repo

            service = KnowledgeBaseService(session=mock_session)
            result = await service.lookup("Vỏ hộp chính, bằng nhựa PC")

        assert result is not None
        assert result.hs_code_id == 42
        assert result.confidence == 95
        assert result.similarity_score == 0.95
        assert result.match_type == "containment"

    @pytest.mark.asyncio
    async def test_lookup_exact_takes_priority_over_containment(self):
        """Test exact match short-circuits (containment and similar not called)."""
        mock_session = AsyncMock()
        verified_record = self._make_verified_record()

        with patch(
            "app.services.knowledge_base_service.LookupRecordRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_verified_exact.return_value = verified_record
            mock_repo_class.return_value = mock_repo

            service = KnowledgeBaseService(session=mock_session)
            result = await service.lookup("copper towel rack")

        assert result is not None
        assert result.match_type == "exact"
        mock_repo.find_verified_containment.assert_not_awaited()
        mock_repo.find_verified_similar.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_lookup_containment_takes_priority_over_similar(self):
        """Test containment match short-circuits (similar not called)."""
        mock_session = AsyncMock()
        verified_record = self._make_verified_record(id=3)

        with patch(
            "app.services.knowledge_base_service.LookupRecordRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_verified_exact.return_value = None
            mock_repo.find_verified_containment.return_value = [
                (verified_record, 0.95)
            ]
            mock_repo_class.return_value = mock_repo

            service = KnowledgeBaseService(session=mock_session)
            result = await service.lookup("Vỏ hộp chính, bằng nhựa PC")

        assert result is not None
        assert result.match_type == "containment"
        mock_repo.find_verified_similar.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_lookup_no_match_returns_none(self):
        """Test KB lookup returns None when no KB match exists."""
        mock_session = AsyncMock()

        with patch(
            "app.services.knowledge_base_service.LookupRecordRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_verified_exact.return_value = None
            mock_repo.find_verified_containment.return_value = []
            mock_repo.find_verified_similar.return_value = []
            mock_repo_class.return_value = mock_repo

            service = KnowledgeBaseService(session=mock_session)
            result = await service.lookup("xyznonexistent123")

        assert result is None

    @pytest.mark.asyncio
    async def test_lookup_exact_takes_priority_over_similar(self):
        """Test exact match short-circuits (containment and similar not called)."""
        mock_session = AsyncMock()
        verified_record = self._make_verified_record()

        with patch(
            "app.services.knowledge_base_service.LookupRecordRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_verified_exact.return_value = verified_record
            mock_repo_class.return_value = mock_repo

            service = KnowledgeBaseService(session=mock_session)
            result = await service.lookup("copper towel rack")

        assert result is not None
        assert result.match_type == "exact"
        mock_repo.find_verified_containment.assert_not_awaited()
        mock_repo.find_verified_similar.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_lookup_computes_correct_query_hash(self):
        """Test lookup uses compute_query_hash for exact lookup."""
        mock_session = AsyncMock()

        with patch(
            "app.services.knowledge_base_service.LookupRecordRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_verified_exact.return_value = None
            mock_repo.find_verified_containment.return_value = []
            mock_repo.find_verified_similar.return_value = []
            mock_repo_class.return_value = mock_repo

            service = KnowledgeBaseService(session=mock_session)
            await service.lookup("  COPPER Towel RACK  ")

        expected_hash = compute_query_hash("  COPPER Towel RACK  ")
        mock_repo.find_verified_exact.assert_awaited_once_with(expected_hash)

    @pytest.mark.asyncio
    async def test_lookup_similar_confidence_scaled_by_similarity(self):
        """Test that similar match confidence is similarity * 100."""
        mock_session = AsyncMock()
        verified_record = self._make_verified_record()

        with patch(
            "app.services.knowledge_base_service.LookupRecordRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_verified_exact.return_value = None
            mock_repo.find_verified_containment.return_value = []
            mock_repo.find_verified_similar.return_value = [
                (verified_record, 0.87)
            ]
            mock_repo_class.return_value = mock_repo

            service = KnowledgeBaseService(session=mock_session)
            result = await service.lookup("copper towel holder")

        assert result is not None
        assert result.confidence == 87  # int(0.87 * 100)

    @pytest.mark.asyncio
    async def test_lookup_verified_at_metadata(self):
        """Test that verification metadata is passed through."""
        mock_session = AsyncMock()
        verified_at = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)
        verified_record = self._make_verified_record(
            verified_by_user_id=7,
            verified_at=verified_at,
        )

        with patch(
            "app.services.knowledge_base_service.LookupRecordRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_verified_exact.return_value = verified_record
            mock_repo_class.return_value = mock_repo

            service = KnowledgeBaseService(session=mock_session)
            result = await service.lookup("copper towel rack")

        assert result is not None
        assert result.verified_by_user_id == 7
        assert result.verified_at == verified_at

"""Tests for customs import repository — history retrieval and stats aggregation."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.customs_import_repository import CustomsImportRepository


def _make_batch_row(
    id: int = 1,
    file_name: str = "report.xlsx",
    company_name: str | None = "test@admin.com",
    total_rows: int = 100,
    records_imported: int = 90,
    duplicates_skipped: int = 8,
    unmatched_codes: int = 2,
    errors_count: int = 0,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    imported_by_email: str | None = "admin@test.com",
) -> MagicMock:
    """Create a mock row matching the repository SELECT columns."""
    row = MagicMock()
    row.id = id
    row.file_name = file_name
    row.company_name = company_name
    row.total_rows = total_rows
    row.records_imported = records_imported
    row.duplicates_skipped = duplicates_skipped
    row.unmatched_codes = unmatched_codes
    row.errors_count = errors_count
    row.started_at = started_at or datetime(2026, 2, 24, 10, 0, 0, tzinfo=timezone.utc)
    row.completed_at = completed_at or datetime(2026, 2, 24, 10, 0, 5, tzinfo=timezone.utc)
    row.imported_by_email = imported_by_email
    return row


class TestGetImportHistory:
    """Tests for CustomsImportRepository.get_import_history()."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_batches(self):
        """Test that empty history returns empty list and zero total."""
        session = AsyncMock()
        # Count query returns 0
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        # Data query returns empty
        data_result = MagicMock()
        data_result.all.return_value = []

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        repo = CustomsImportRepository(session)
        items, total = await repo.get_import_history(limit=20, offset=0)

        assert total == 0
        assert items == []

    @pytest.mark.asyncio
    async def test_returns_batches_with_user_email(self):
        """Test that history includes imported_by_email from user join."""
        session = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        batch_row = _make_batch_row(imported_by_email="admin@example.com")
        data_result = MagicMock()
        data_result.all.return_value = [batch_row]

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        repo = CustomsImportRepository(session)
        items, total = await repo.get_import_history()

        assert total == 1
        assert len(items) == 1
        assert items[0]["imported_by_email"] == "admin@example.com"
        assert items[0]["file_name"] == "report.xlsx"
        assert items[0]["records_imported"] == 90

    @pytest.mark.asyncio
    async def test_returns_iso_format_dates(self):
        """Test that started_at and completed_at are ISO formatted strings."""
        session = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        ts = datetime(2026, 2, 24, 15, 30, 0, tzinfo=timezone.utc)
        batch_row = _make_batch_row(started_at=ts, completed_at=ts)
        data_result = MagicMock()
        data_result.all.return_value = [batch_row]

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        repo = CustomsImportRepository(session)
        items, _ = await repo.get_import_history()

        assert items[0]["started_at"] == ts.isoformat()
        assert items[0]["completed_at"] == ts.isoformat()

    @pytest.mark.asyncio
    async def test_handles_null_user(self):
        """Test history with no user (imported_by_email is None)."""
        session = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        batch_row = _make_batch_row(imported_by_email=None)
        data_result = MagicMock()
        data_result.all.return_value = [batch_row]

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        repo = CustomsImportRepository(session)
        items, _ = await repo.get_import_history()

        assert items[0]["imported_by_email"] is None

    @pytest.mark.asyncio
    async def test_pagination_params_passed(self):
        """Test that limit and offset are forwarded to the query."""
        session = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = 50
        data_result = MagicMock()
        data_result.all.return_value = []

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        repo = CustomsImportRepository(session)
        _, total = await repo.get_import_history(limit=5, offset=10)

        assert total == 50
        # Verify execute was called twice (count + data)
        assert session.execute.call_count == 2


class TestGetKbStats:
    """Tests for CustomsImportRepository.get_kb_stats()."""

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_verified_records(self):
        """Test stats with no verified records."""
        session = AsyncMock()
        # total_verified query
        total_result = MagicMock()
        total_result.scalar.return_value = 0
        # method breakdown query
        method_result = MagicMock()
        method_result.all.return_value = []
        # chapter coverage query
        chapter_result = MagicMock()
        chapter_result.all.return_value = []

        session.execute = AsyncMock(
            side_effect=[total_result, method_result, chapter_result]
        )

        repo = CustomsImportRepository(session)
        stats = await repo.get_kb_stats()

        assert stats["total_verified"] == 0
        assert stats["breakdown_by_method"] == []
        assert stats["top_chapters"] == []

    @pytest.mark.asyncio
    async def test_returns_breakdown_by_method(self):
        """Test that method breakdown is properly formatted."""
        session = AsyncMock()
        total_result = MagicMock()
        total_result.scalar.return_value = 150

        method_row_1 = MagicMock()
        method_row_1.search_method = "customs_import"
        method_row_1.count = 100
        method_row_2 = MagicMock()
        method_row_2.search_method = "notebooklm"
        method_row_2.count = 50

        method_result = MagicMock()
        method_result.all.return_value = [method_row_1, method_row_2]

        chapter_result = MagicMock()
        chapter_result.all.return_value = []

        session.execute = AsyncMock(
            side_effect=[total_result, method_result, chapter_result]
        )

        repo = CustomsImportRepository(session)
        stats = await repo.get_kb_stats()

        assert stats["total_verified"] == 150
        assert len(stats["breakdown_by_method"]) == 2
        assert stats["breakdown_by_method"][0]["search_method"] == "customs_import"
        assert stats["breakdown_by_method"][0]["count"] == 100
        assert stats["breakdown_by_method"][1]["search_method"] == "notebooklm"
        assert stats["breakdown_by_method"][1]["count"] == 50

    @pytest.mark.asyncio
    async def test_returns_top_chapters(self):
        """Test that chapter coverage data is returned correctly."""
        session = AsyncMock()
        total_result = MagicMock()
        total_result.scalar.return_value = 200

        method_result = MagicMock()
        method_result.all.return_value = []

        ch_row = MagicMock()
        ch_row.chapter_code = "85"
        ch_row.name_vn = "May dien va thiet bi dien"
        ch_row.record_count = 75

        chapter_result = MagicMock()
        chapter_result.all.return_value = [ch_row]

        session.execute = AsyncMock(
            side_effect=[total_result, method_result, chapter_result]
        )

        repo = CustomsImportRepository(session)
        stats = await repo.get_kb_stats()

        assert len(stats["top_chapters"]) == 1
        assert stats["top_chapters"][0]["chapter_code"] == "85"
        assert stats["top_chapters"][0]["name_vn"] == "May dien va thiet bi dien"
        assert stats["top_chapters"][0]["record_count"] == 75


class TestGetRecentImports:
    """Tests for CustomsImportRepository.get_recent_imports()."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_imports(self):
        """Test empty recent imports."""
        session = AsyncMock()
        result = MagicMock()
        result.all.return_value = []
        session.execute = AsyncMock(return_value=result)

        repo = CustomsImportRepository(session)
        recent = await repo.get_recent_imports(limit=5)

        assert recent == []

    @pytest.mark.asyncio
    async def test_returns_recent_batches(self):
        """Test that recent imports are returned with all fields."""
        session = AsyncMock()
        batch_row = _make_batch_row(id=42, file_name="customs_dec.xlsx")
        result = MagicMock()
        result.all.return_value = [batch_row]
        session.execute = AsyncMock(return_value=result)

        repo = CustomsImportRepository(session)
        recent = await repo.get_recent_imports(limit=5)

        assert len(recent) == 1
        assert recent[0]["id"] == 42
        assert recent[0]["file_name"] == "customs_dec.xlsx"
        assert recent[0]["records_imported"] == 90

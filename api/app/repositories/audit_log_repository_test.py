"""Tests for audit log repository."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository


class TestAuditLogRepository:
    """Tests for AuditLogRepository."""

    def _make_repo(self) -> tuple[AuditLogRepository, AsyncMock]:
        """Create an AuditLogRepository with a mock session."""
        session = AsyncMock()
        repo = AuditLogRepository(session)
        return repo, session

    @pytest.mark.asyncio
    async def test_create_audit_log_entry(self):
        """Test creating an audit log entry adds it to session and flushes."""
        repo, session = self._make_repo()

        result = await repo.create(
            admin_user_id=1,
            action="role_change",
            target_user_id=2,
            details={"old_role": "user", "new_role": "admin"},
        )

        session.add.assert_called_once()
        session.flush.assert_awaited_once()
        added_entry = session.add.call_args[0][0]
        assert isinstance(added_entry, AuditLog)
        assert added_entry.admin_user_id == 1
        assert added_entry.action == "role_change"
        assert added_entry.target_user_id == 2
        assert added_entry.details == {"old_role": "user", "new_role": "admin"}

    @pytest.mark.asyncio
    async def test_list_recent_returns_entries(self):
        """Test list_recent returns entries in descending order."""
        repo, session = self._make_repo()

        entry1 = AuditLog(id=1, admin_user_id=1, action="role_change")
        entry2 = AuditLog(id=2, admin_user_id=1, action="role_change")

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [entry2, entry1]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        session.execute.return_value = mock_result

        entries = await repo.list_recent()

        assert len(entries) == 2
        assert entries[0] is entry2
        assert entries[1] is entry1

    @pytest.mark.asyncio
    async def test_list_recent_respects_limit(self):
        """Test list_recent respects the limit parameter."""
        repo, session = self._make_repo()

        entry1 = AuditLog(id=1, admin_user_id=1, action="role_change")

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [entry1]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        session.execute.return_value = mock_result

        entries = await repo.list_recent(limit=1)

        assert len(entries) == 1
        session.execute.assert_awaited_once()

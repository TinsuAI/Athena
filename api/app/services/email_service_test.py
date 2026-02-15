"""Tests for email service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.email_service import EmailService


@pytest.fixture
def settings():
    """Create mock settings for email service."""
    s = MagicMock()
    s.smtp_host = "localhost"
    s.smtp_port = 1025
    s.smtp_user = ""
    s.smtp_password = ""
    s.smtp_from_email = "noreply@athena.local"
    s.smtp_use_tls = False
    return s


class TestEmailService:
    """Tests for EmailService."""

    @pytest.mark.asyncio
    async def test_send_password_reset_email_calls_smtp(self, settings):
        """Test that send_password_reset_email sends an email via SMTP."""
        with patch("app.services.email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            service = EmailService(settings)
            await service.send_password_reset_email(
                "user@example.com", "https://athena.local/reset-password?token=abc123"
            )

            mock_send.assert_awaited_once()
            call_kwargs = mock_send.call_args
            message = call_kwargs[0][0]

            assert message["To"] == "user@example.com"
            assert message["From"] == "noreply@athena.local"
            assert "Password Reset" in message["Subject"]

    @pytest.mark.asyncio
    async def test_send_password_reset_email_contains_reset_url(self, settings):
        """Test that the email body contains the reset URL."""
        with patch("app.services.email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            service = EmailService(settings)
            reset_url = "https://athena.local/reset-password?token=abc123"
            await service.send_password_reset_email("user@example.com", reset_url)

            message = mock_send.call_args[0][0]
            body = message.get_content()
            assert reset_url in body
            assert "1 hour" in body

    @pytest.mark.asyncio
    async def test_send_password_reset_email_smtp_config(self, settings):
        """Test that SMTP connection uses correct config."""
        with patch("app.services.email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            service = EmailService(settings)
            await service.send_password_reset_email(
                "user@example.com", "https://athena.local/reset-password?token=abc"
            )

            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["hostname"] == "localhost"
            assert call_kwargs["port"] == 1025
            assert call_kwargs["start_tls"] is False

    @pytest.mark.asyncio
    async def test_send_password_reset_email_smtp_error_propagates(self, settings):
        """Test that SMTP connection errors propagate to caller."""
        with patch(
            "app.services.email_service.aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=ConnectionRefusedError("Connection refused"),
        ):
            service = EmailService(settings)
            with pytest.raises(ConnectionRefusedError):
                await service.send_password_reset_email(
                    "user@example.com", "https://athena.local/reset-password?token=abc"
                )

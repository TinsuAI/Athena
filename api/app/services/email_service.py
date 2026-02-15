"""Email service for sending transactional emails."""

import logging
from email.message import EmailMessage

import aiosmtplib

from app.core.config import Settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self, settings: Settings):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.user = settings.smtp_user
        self.password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.use_tls = settings.smtp_use_tls

    async def send_password_reset_email(self, to_email: str, reset_url: str) -> None:
        """Send a password reset email with the given reset URL.

        Args:
            to_email: Recipient email address.
            reset_url: Full URL for the password reset page with token.
        """
        message = EmailMessage()
        message["From"] = self.from_email
        message["To"] = to_email
        message["Subject"] = "Athena - Password Reset Request"
        message.set_content(
            f"You requested a password reset for your Athena account.\n"
            f"\n"
            f"Click the link below to reset your password. This link is valid for 1 hour.\n"
            f"\n"
            f"{reset_url}\n"
            f"\n"
            f"If you did not request this, please ignore this email.\n"
        )

        await aiosmtplib.send(
            message,
            hostname=self.host,
            port=self.port,
            username=self.user or None,
            password=self.password or None,
            start_tls=self.use_tls,
            timeout=30,  # 30 second timeout to prevent hanging
        )
        logger.info("Password reset email sent to %s", to_email)

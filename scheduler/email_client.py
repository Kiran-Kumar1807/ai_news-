"""Gmail SMTP email client."""
from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.config import settings
from backend.logging_config import get_logger

logger = get_logger("email")


def send_email(to_address: str, subject: str, html_body: str, text_body: str = "") -> bool:
    """Send an email via SMTP. Returns True on success.

    If SMTP credentials are not configured the email is logged and skipped so
    that the scheduler can run in development without a mail account.
    """
    if not settings.smtp_enabled:
        logger.info(
            "SMTP disabled; skipping email",
            extra={"ctx_to": to_address, "ctx_subject": subject},
        )
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = to_address
    if text_body:
        message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.smtp_username, [to_address], message.as_string())
        logger.info("Email sent", extra={"ctx_to": to_address})
        return True
    except Exception as exc:  # pragma: no cover - network errors
        logger.error(
            "Failed to send email",
            extra={"ctx_to": to_address, "ctx_error": str(exc)},
        )
        return False

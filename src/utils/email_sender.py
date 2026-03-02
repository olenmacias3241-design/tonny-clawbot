"""Email sending utility using SMTP."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Union
from src.utils.config import get_settings
from src.utils.logger import log


class EmailSender:
    """Email sender using SMTP."""

    def __init__(self):
        self.settings = get_settings()
        self._validate_config()

    def _validate_config(self):
        """Validate email configuration."""
        if not self.settings.smtp_username:
            log.warning("SMTP_USERNAME not configured - email sending disabled")
        if not self.settings.smtp_password:
            log.warning("SMTP_PASSWORD not configured - email sending disabled")

    def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Email body (plain text or HTML)
            html: Whether body is HTML
            cc: CC recipients
            bcc: BCC recipients

        Returns:
            True if email was sent successfully
        """
        if not self.settings.smtp_username or not self.settings.smtp_password:
            log.error("Email credentials not configured")
            return False

        try:
            # Convert single recipient to list
            recipients = [to] if isinstance(to, str) else to

            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.settings.email_from or self.settings.smtp_username
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = ", ".join(cc)
                recipients.extend(cc)

            if bcc:
                recipients.extend(bcc)

            # Attach body
            mime_type = "html" if html else "plain"
            msg.attach(MIMEText(body, mime_type))

            # Send email
            with smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port) as server:
                server.starttls()
                server.login(self.settings.smtp_username, self.settings.smtp_password)
                server.send_message(msg)

            log.info(f"Email sent successfully to {recipients}")
            return True

        except Exception as e:
            log.error(f"Failed to send email: {e}")
            return False

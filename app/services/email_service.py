"""
Email Service for Nexus

Handles sending emails for user registration, password resets, and notifications.
Supports multiple email providers:
- Local SMTP (sendmail, postfix)
- Gmail/OAuth
- AWS SES
- Brevo (Sendinblue)
- Custom SMTP servers
"""

import smtplib
import asyncio
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP or API."""

    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.sender_email = settings.SENDER_EMAIL
        self.admin_email = settings.ADMIN_EMAIL
        self.brevo_api_key = getattr(settings, "BREVO_API_KEY", None)

    def _send_via_smtp(
        self,
        recipient: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> bool:
        """Send email via SMTP."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = recipient

            if body_text:
                msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))

            if self.smtp_user and self.smtp_password:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.send_message(msg)

            safe_recipient = recipient.replace("\n", "").replace("\r", "")
            logger.info(f"✅ Email sent to {safe_recipient}")
            return True

        except Exception as e:
            safe_recipient = recipient.replace("\n", "").replace("\r", "")
            safe_error = str(e).replace("\n", "").replace("\r", "")
            logger.error(
                f"❌ Failed to send email via SMTP to {safe_recipient}: {safe_error}"
            )
            return False

    def _send_via_brevo(
        self,
        recipient: str,
        subject: str,
        body_html: str,
        recipient_name: Optional[str] = None,
    ) -> bool:
        """Send email via Brevo API."""
        if not self.brevo_api_key:
            logger.warning("Brevo API key not configured, falling back to SMTP")
            return False

        try:
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "accept": "application/json",
                "api-key": self.brevo_api_key,
                "content-type": "application/json",
            }
            data = {
                "sender": {"name": "Nexus", "email": self.sender_email},
                "to": [{"email": recipient, "name": recipient_name or recipient}],
                "subject": subject,
                "htmlContent": body_html,
            }
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()

            safe_recipient = recipient.replace("\n", "").replace("\r", "")
            logger.info(f"✅ Email sent to {safe_recipient} via Brevo")
            return True

        except Exception as e:
            safe_recipient = recipient.replace("\n", "").replace("\r", "")
            safe_error = str(e).replace("\n", "").replace("\r", "")
            logger.error(
                f"❌ Failed to send email via Brevo to {safe_recipient}: {safe_error}"
            )
            return False

    def send_email(
        self,
        recipient: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        recipient_name: Optional[str] = None,
    ) -> bool:
        """
        Send email using configured provider.

        Args:
            recipient: Email address
            subject: Email subject
            body_html: HTML body
            body_text: Optional plain text fallback
            recipient_name: Recipient's name

        Returns:
            True if successful, False otherwise
        """
        # Try Brevo if configured
        if self.brevo_api_key:
            if self._send_via_brevo(recipient, subject, body_html, recipient_name):
                return True

        # Fall back to SMTP
        return self._send_via_smtp(recipient, subject, body_html, body_text)

    async def send_email_async(
        self,
        recipient: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        recipient_name: Optional[str] = None,
    ) -> bool:
        """Send email asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.send_email,
            recipient,
            subject,
            body_html,
            body_text,
            recipient_name,
        )

    def send_registration_email(self, to_email: str, username: str) -> bool:
        """Send welcome email to newly registered user."""
        subject = "Welcome to Nexus! 🚀"

        body_text = f"""
Welcome to Nexus, {username}!

Thank you for registering. Your account has been created successfully.

You can now log in and start personalizing your news feed.

If you have any questions or need assistance, please contact us at {self.admin_email}.

Happy reading!
The Nexus Team
"""

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #007bff; color: white; padding: 20px; border-radius: 5px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f8f9fa; border-radius: 5px; margin-top: 20px; }}
        .footer {{ margin-top: 20px; font-size: 12px; color: #666; text-align: center; }}
        .button {{ display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 3px; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to Nexus! 🚀</h1>
        </div>
        
        <div class="content">
            <p>Hello <strong>{username}</strong>,</p>
            
            <p>Thank you for registering with Nexus! Your account has been created successfully.</p>
            
            <p>You can now log in and start personalizing your news feed with the topics and sources you care about.</p>
            
            <p>
                <a href="https://comdat.ca" class="button">Go to Nexus</a>
            </p>
            
            <p>If you have any questions or need assistance, please don't hesitate to reach out to us.</p>
        </div>
        
        <div class="footer">
            <p>Best regards,<br>The Nexus Team</p>
            <p><small>If you did not create this account, please contact us immediately at {self.admin_email}</small></p>
        </div>
    </div>
</body>
</html>
"""

        return self.send_email(to_email, subject, body_html, body_text, username)

    async def send_registration_email_async(self, to_email: str, username: str) -> bool:
        """Send registration email asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.send_registration_email, to_email, username
        )


# Global instance
email_service = EmailService()

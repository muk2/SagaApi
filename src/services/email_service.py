from __future__ import annotations

import logging
import smtplib
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending transactional emails.

    Failures are logged but never raised - email should never block
    the payment response.

    Usage with FastAPI BackgroundTasks:
        @router.post("/register")
        def register(background_tasks: BackgroundTasks):
            # ... process registration ...
            background_tasks.add_task(
                email_service.send_event_registration_receipt,
                to_email=user_email,
                event_name=event.name,
                event_date=str(event.date),
                amount=amount,
                card_last_four=card_last_four,
                registration_id=registration.id,
            )
    """

    def _send_email(self, to_email: str, subject: str, text_body: str, html_body: str) -> bool:
        """Send an email via SMTP. Returns True on success, False on failure."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            if settings.SMTP_SSL:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                server.ehlo()
                if settings.SMTP_TLS:
                    server.starttls()
                    server.ehlo()

            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            logger.info("Email sent successfully to %s: %s", to_email, subject)
            return True
        except Exception:
            logger.exception("Failed to send email to %s: %s", to_email, subject)
            return False

    def send_event_registration_receipt(
        self,
        to_email: str,
        event_name: str,
        event_date: str,
        amount: Decimal,
        card_last_four: str,
        registration_id: int,
    ) -> bool:
        """Send event registration confirmation receipt."""
        subject = f"SAGA Golf — Registration Confirmation for {event_name}"

        text_body = (
            f"Registration Confirmation\n\n"
            f"Event: {event_name}\n"
            f"Date: {event_date}\n"
            f"Amount Charged: ${amount:.2f}\n"
            f"Card: ****{card_last_four}\n"
            f"Registration ID: {registration_id}\n\n"
            f"Thank you for registering with SAGA Golf!"
        )

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #2d5016; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">SAGA Golf</h1>
            </div>
            <div style="padding: 20px; background-color: #f9f9f9;">
                <h2>Registration Confirmation</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td style="padding: 8px; font-weight: bold;">Event</td><td style="padding: 8px;">{event_name}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">Date</td><td style="padding: 8px;">{event_date}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">Amount Charged</td><td style="padding: 8px;">${amount:.2f}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">Card</td><td style="padding: 8px;">****{card_last_four}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">Registration ID</td><td style="padding: 8px;">{registration_id}</td></tr>
                </table>
                <p style="margin-top: 20px;">Thank you for registering with SAGA Golf!</p>
            </div>
            <div style="padding: 10px; text-align: center; color: #666; font-size: 12px;">
                <p>SAGA Golf — A Non-Profit Golf Organization</p>
            </div>
        </body>
        </html>
        """

        return self._send_email(to_email, subject, text_body, html_body)

    def send_membership_receipt(
        self,
        to_email: str,
        tier_name: str,
        season_year: int,
        amount: Decimal,
        card_last_four: str,
    ) -> bool:
        """Send membership payment confirmation receipt."""
        subject = "SAGA Golf — Membership Payment Confirmation"

        text_body = (
            f"Membership Payment Confirmation\n\n"
            f"Tier: {tier_name}\n"
            f"Season: {season_year}\n"
            f"Amount Charged: ${amount:.2f}\n"
            f"Card: ****{card_last_four}\n\n"
            f"Thank you for your membership with SAGA Golf!"
        )

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #2d5016; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">SAGA Golf</h1>
            </div>
            <div style="padding: 20px; background-color: #f9f9f9;">
                <h2>Membership Payment Confirmation</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td style="padding: 8px; font-weight: bold;">Membership Tier</td><td style="padding: 8px;">{tier_name}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">Season Year</td><td style="padding: 8px;">{season_year}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">Amount Charged</td><td style="padding: 8px;">${amount:.2f}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">Card</td><td style="padding: 8px;">****{card_last_four}</td></tr>
                </table>
                <p style="margin-top: 20px;">Thank you for your membership with SAGA Golf!</p>
            </div>
            <div style="padding: 10px; text-align: center; color: #666; font-size: 12px;">
                <p>SAGA Golf — A Non-Profit Golf Organization</p>
            </div>
        </body>
        </html>
        """

        return self._send_email(to_email, subject, text_body, html_body)
